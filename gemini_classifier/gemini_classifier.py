import pandas as pd
import google.generativeai as genai
import json
import os
import time
import sys
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
            if not response.candidates:
                block_reason = response.prompt_feedback.block_reason
                print(f"Warning: Batch blocked on attempt {attempt + 1}. Reason: {block_reason}. Retrying...")
                time.sleep(3 * (attempt + 1))
                continue
            cleaned_response = response.text.strip()
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
        time.sleep(3 * (attempt + 1))
    print("ERROR: Failed to get a valid response from Gemini after 3 attempts for a batch.")
    return None

def format_for_label_studio(comment_text, label, model_version="gemini-1.5-pro-latest"):
    """Formats a single comment and its predicted label into the Label Studio JSON format."""
    return {
        "data": {"text": comment_text},
        "predictions": [{
            "model_version": model_version,
            "result": [{
                "from_name": "sentiment", "to_name": "text", "type": "choices",
                "value": {"choices": [label]}
            }]
        }]
    }

def save_progress(tasks, path):
    """Saves the list of processed tasks to a JSON file."""
    print(f"\nSaving {len(tasks)} processed tasks to {path}...")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        print("Progress saved successfully.")
    except IOError as e:
        print(f"ERROR: Could not write to file '{path}'. Error: {e}")

def load_progress(path):
    """Loads existing tasks from a JSON file if it exists."""
    if not os.path.exists(path):
        print("No existing output file found. Starting fresh.")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        print(f"Loaded {len(tasks)} tasks from existing file '{path}'.")
        return tasks
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read or parse existing file '{path}'. Starting fresh. Error: {e}")
        return []

def analyze_comments(input_csv, output_json, batch_size, api_key, model_name, limit=None, start_from=None, end_at=None):
    """Main function to load, process, analyze, and format comments with rate limiting and resume support."""
    if not configure_gemini(api_key):
        return

    # 1. Load existing progress to support resuming
    ls_tasks = load_progress(output_json)
    processed_comments = {task['data']['text'] for task in ls_tasks}

    # 2. Load and clean the source data
    print(f"\nReading data from {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{input_csv}'")
        return
        
    df.dropna(subset=['Comment'], inplace=True)
    df = df[~df['Comment'].isin(['[deleted]', '[removed]'])]
    df = df[~df['Author'].isin(['AutoModerator'])]
    df.reset_index(drop=True, inplace=True)
    
    # 3. Handle user-defined processing ranges
    if start_from is not None or end_at is not None:
        start = start_from or 0
        end = end_at or len(df)
        print(f"Slicing DataFrame to user-specified range: rows {start} to {end}.")
        df = df.iloc[start:end].copy()
    
    # 4. Filter out comments that have already been processed
    initial_count = len(df)
    df = df[~df['Comment'].isin(processed_comments)]
    if initial_count > len(df):
        print(f"Resuming... Skipped {initial_count - len(df)} already processed comments.")

    if limit and not (start_from or end_at):
        df = df.head(limit)

    if df.empty:
        print("No new comments to process. Exiting.")
        return

    print(f"Found {len(df)} new comments to process.")
    
    model = genai.GenerativeModel(model_name=model_name, generation_config={"temperature": 0.1})
    
    # 5. Main processing loop with graceful shutdown
    try:
        print(f"Processing in batches of {batch_size} using model '{model_name}'...")
        for i in tqdm(range(0, len(df), batch_size), desc="Analyzing Batches"):
            batch_df = df.iloc[i:i + batch_size]
            comments_to_analyze = batch_df['Comment'].tolist()
            sentiments = get_sentiments_from_gemini(comments_to_analyze, model)

            if sentiments:
                for comment, sentiment in zip(comments_to_analyze, sentiments):
                    valid_labels = ['positive', 'negative', 'neutral']
                    if sentiment not in valid_labels:
                        sentiment = 'neutral'
                    ls_tasks.append(format_for_label_studio(comment, sentiment, model_version=model_name))
            else:
                print(f"Skipping batch starting at index {i} due to API failure. Progress will be saved on exit.")

            # Rate Limiting: 10 RPM = 1 request every 6 seconds. Add a small buffer.
            time.sleep(6.1)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving progress...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}. Saving progress...")
    finally:
        save_progress(ls_tasks, output_json)
        print("\nProcess finished.")

if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Analyzes comment sentiment using the Gemini API and creates a Label Studio file."
    )
    
    parser.add_argument("-i", "--input_csv", required=True, help="Path to the input CSV file.")
    parser.add_argument("-o", "--output_json", required=True, help="Path for the output Label Studio JSON file.")
    
    parser.add_argument("-b", "--batch_size", type=int, default=10, help="Number of comments per API call.")
    parser.add_argument("-k", "--api_key", type=str, default=None, help="Google Gemini API key. Can be set via .env or GEMINI_API_KEY.")
    parser.add_argument("-m", "--model_name", type=str, default=None, help="Gemini model name. Can be set via .env or GEMINI_MODEL_NAME.")
    
    # New arguments for resuming and slicing
    parser.add_argument("-l", "--limit", type=int, default=None, help="Limit the number of new comments to process (for quick tests).")
    parser.add_argument("--start-from", type=int, default=None, help="The starting row index of the CSV to process.")
    parser.add_argument("--end-at", type=int, default=None, help="The ending row index (exclusive) of the CSV to process.")
    
    args = parser.parse_args()

    gemini_api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    gemini_model_name = args.model_name or os.getenv("GEMINI_MODEL_NAME") or "gemini-1.5-flash-latest"
    
    if not gemini_api_key:
        try:
            gemini_api_key = input("Gemini API key not found. Please enter your key: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit()
            
    if not gemini_api_key:
        print("No API key provided. Exiting.")
    else:
        analyze_comments(args.input_csv, args.output_json, args.batch_size, gemini_api_key, gemini_model_name, args.limit, args.start_from, args.end_at)