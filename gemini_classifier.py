import pandas as pd
import google.generativeai as genai
import json
import os
import time
from tqdm import tqdm
import argparse
from dotenv import load_dotenv

def configure_gemini(api_key):
    """Configures the Gemini API with the provided key."""
    try:
        genai.configure(api_key=api_key)
        print("Gemini API configured successfully.")
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return False

def get_sentiments_from_gemini(comments_batch, model):
    """
    Sends a batch of comments to the Gemini API and gets sentiment predictions.
    Includes robust error handling and retry logic.

    Args:
        comments_batch (list): A list of comment strings.
        model: The configured Gemini model instance.

    Returns:
        A list of predicted sentiment strings or None if an error occurs.
    """
    prompt = f"""
    You are an expert sentiment analysis AI.
    Analyze the following list of user comments regarding AI's impact on employment.
    Classify each comment into one of three categories: 'positive', 'negative', or 'neutral'.

    Classification Guidelines:
    - 'positive': Supports or is optimistic about AI replacing jobs.
    - 'negative': Expresses fear, opposition, or concern about AI replacing jobs.
    - 'neutral': Off-topic, a question, a joke, a link, or has no clear sentiment on the topic.

    Output Format:
    You MUST respond with ONLY a valid JSON array of strings. The array must have the exact same number of items as the input array, in the same order.
    Example: ["negative", "positive", "neutral"]

    Input Comments:
    {json.dumps(comments_batch, indent=2)}
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)

            # --- MODERN SDK ERROR HANDLING ---
            # Check if the response was blocked or did not produce candidates
            if not response.candidates:
                block_reason = response.prompt_feedback.block_reason
                print(f"Warning: Batch blocked on attempt {attempt + 1}. Reason: {block_reason}. Retrying...")
                time.sleep(3 * (attempt + 1))
                continue

            cleaned_response = response.text.strip()
            
            # Additional cleanup for cases where the model might still add markdown
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3].strip()
            
            sentiments = json.loads(cleaned_response)
            
            if isinstance(sentiments, list) and len(sentiments) == len(comments_batch):
                return sentiments
            else:
                print(f"Warning: Response length mismatch. Expected {len(comments_batch)}, got {len(sentiments)}. Retrying...")
        
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to decode JSON on attempt {attempt + 1}. Response was: '{cleaned_response}'. Error: {e}")
        except Exception as e:
            print(f"Warning: An unexpected API error occurred on attempt {attempt + 1}: {e}")
        
        time.sleep(3 * (attempt + 1)) # Exponential backoff

    print("ERROR: Failed to get a valid response from Gemini after 3 attempts for a batch.")
    return None

def format_for_label_studio(comment_text, label, model_version="gemini-1.5-pro-latest"):
    """
    Formats a single comment and its predicted label into the Label Studio JSON format.
    """
    return {
        "data": {
            "text": comment_text
        },
        "predictions": [{
            "model_version": model_version,
            "result": [{
                "from_name": "sentiment",
                "to_name": "text",
                "type": "choices",
                "value": {
                    "choices": [label]
                }
            }]
        }]
    }

def analyze_comments(input_csv_path, output_json_path, batch_size, api_key, model_name, limit=None):
    """
    Main function to load, process, analyze, and format comments.
    """
    if not configure_gemini(api_key):
        return

    print(f"\nReading data from {input_csv_path}...")
    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{input_csv_path}'")
        return
        
    df.dropna(subset=['Comment'], inplace=True)
    df = df[~df['Comment'].isin(['[deleted]', '[removed]'])]
    df = df[~df['Author'].isin(['AutoModerator'])]
    df.reset_index(drop=True, inplace=True)

    if limit:
        print(f"Processing a limited number of rows: {limit}")
        df = df.head(limit)

    print(f"Found {len(df)} valid comments to process.")
    
    generation_config = {"temperature": 0.1, "top_p": 0.95}
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )
    
    ls_tasks = []
    
    print(f"Processing in batches of {batch_size} using model '{model_name}'...")
    for i in tqdm(range(0, len(df), batch_size), desc="Analyzing Batches"):
        batch_df = df.iloc[i:i + batch_size]
        comments_to_analyze = batch_df['Comment'].tolist()
        sentiments = get_sentiments_from_gemini(comments_to_analyze, model)

        if sentiments:
            for comment, sentiment in zip(comments_to_analyze, sentiments):
                valid_labels = ['positive', 'negative', 'neutral']
                if sentiment not in valid_labels:
                    print(f"Warning: Received invalid label '{sentiment}'. Defaulting to 'neutral'.")
                    sentiment = 'neutral'
                ls_task = format_for_label_studio(comment, sentiment, model_version=model_name)
                ls_tasks.append(ls_task)
        else:
            print(f"Skipping batch starting at index {i} due to API failure.")

    print(f"\nSaving {len(ls_tasks)} pre-annotated tasks to {output_json_path}...")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(ls_tasks, f, ensure_ascii=False, indent=2)

    print("\nProcess finished successfully!")


if __name__ == '__main__':
    load_dotenv() # Load variables from a .env file into the environment
    
    parser = argparse.ArgumentParser(
        description="Analyzes comments for sentiment using the Gemini API and creates a Label Studio pre-annotation file."
    )
    
    parser.add_argument("-i", "--input_csv", help="Path to the input CSV file (e.g., 'reddit_comments.csv')", required=True)
    parser.add_argument("-o", "--output_json", help="Path for the output Label Studio JSON file (e.g., 'pre-annotations.json')", required=True)
    
    parser.add_argument("-b", "--batch_size", type=int, default=10, help="Number of comments to process in each API call (default: 10).")
    parser.add_argument("-k", "--api_key", type=str, default=None, help="Your Google Gemini API key. Can also be set via a .env file or GEMINI_API_KEY environment variable.")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Limit the number of comments to process (for testing).")
    parser.add_argument("-m", "--model_name", type=str, default=None, help="The Gemini model name to use (e.g., 'gemini-1.5-flash-latest'). Can also be set via GEMINI_MODEL_NAME environment variable.")
    
    args = parser.parse_args()

    # --- API Key and Model Name Handling (with .env support) ---
    gemini_api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    gemini_model_name = args.model_name or os.getenv("GEMINI_MODEL_NAME") or "gemini-1.5-flash-latest"
    
    if not gemini_api_key:
        print("Gemini API key not found.")
        try:
            gemini_api_key = input("Please enter your Gemini API key: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            exit()
            
    if not gemini_api_key:
        print("No API key provided. Exiting.")
    else:
        analyze_comments(args.input_csv, args.output_json, args.batch_size, gemini_api_key, gemini_model_name, args.limit)