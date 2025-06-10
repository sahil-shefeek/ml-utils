import os
import csv
import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from tqdm import tqdm

def initialize_youtube_api(api_key):
    """Initializes and returns a YouTube API service object."""
    try:
        # Suppress the "file_cache is only supported when either oauth2client" warning
        # which is not relevant for API key authentication.
        return build('youtube', 'v3', developerKey=api_key, cache_discovery=False)
    except Exception as e:
        print(f"❌ Error initializing YouTube API: {e}")
        return None

def scrape_comments(youtube, video_id, include_replies=False, limit=None):
    """
    Scrapes comments from a YouTube video.

    Args:
        youtube: Initialized YouTube API service object.
        video_id (str): The ID of the YouTube video.
        include_replies (bool): Whether to fetch replies to comments.
        limit (int, optional): Maximum number of comments to fetch. Defaults to None (all).

    Returns:
        A list of dictionaries, where each dictionary represents a comment.
        Returns an empty list if an error occurs.
    """
    comments = []
    pbar = None

    try:
        # Get total comment count for the progress bar
        video_response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        if not video_response.get('items'):
            print(f"⚠️ Video with ID '{video_id}' not found.")
            return []
            
        if 'commentCount' not in video_response['items'][0]['statistics']:
             print(f"ℹ️ Comments are disabled for video ID: {video_id}")
             return []

        total_comments = int(video_response['items'][0]['statistics']['commentCount'])
        print(f"▶️ Found approximately {total_comments} comments. Starting scrape...")
        pbar = tqdm(total=total_comments, desc="Scraping Comments")

        next_page_token = None
        while True:
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                pageToken=next_page_token,
                maxResults=100,
                textFormat='plainText'
            )
            response = request.execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'Author': comment['authorDisplayName'],
                    'Comment': comment['textDisplay'],
                    'Timestamp': comment['publishedAt'],
                    'Likes': comment['likeCount']
                })
                pbar.update(1)

                if limit and len(comments) >= limit:
                    break
                
                # Fetch replies if requested and available
                if include_replies and item.get('replies'):
                    for reply_item in item['replies']['comments']:
                        reply = reply_item['snippet']
                        comments.append({
                            'Author': reply['authorDisplayName'],
                            'Comment': reply['textDisplay'],
                            'Timestamp': reply['publishedAt'],
                            'Likes': reply['likeCount']
                        })
                        pbar.update(1) # Note: this may make the total > initial count
                        if limit and len(comments) >= limit:
                            break
                
                if limit and len(comments) >= limit:
                    break

            if limit and len(comments) >= limit:
                print(f"\n✅ Reached comment limit of {limit}.")
                break
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

    except HttpError as e:
        if "commentsDisabled" in str(e):
            print(f"\nℹ️ Comments are disabled for video ID: {video_id}")
        elif "quotaExceeded" in str(e):
            print("\n❌ QUOTA EXCEEDED. You have run out of API requests for the day.")
        else:
            print(f"\n❌ An HTTP error occurred: {e}")
        return comments # Return what was collected so far
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        return comments # Return what was collected so far
    finally:
        if pbar:
            pbar.close()

    return comments

def save_to_csv(comments_data, output_path):
    """Saves a list of comment dictionaries to a CSV file."""
    if not comments_data:
        print("ℹ️ No comments to save.")
        return

    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as file:
            # Using DictWriter to handle dictionaries directly
            fieldnames = ['Author', 'Comment', 'Timestamp', 'Likes']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for comment in comments_data:
                writer.writerow(comment)
        print(f"✅ Successfully saved {len(comments_data)} comments to '{output_path}'")
    except IOError as e:
        print(f"❌ Error saving file: {e}")

if __name__ == '__main__':
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(
        description="Scrape comments from a YouTube video and save to a CSV file."
    )
    
    parser.add_argument("-v", "--video_id", help="The ID of the YouTube video (e.g., YP8mV_2RDLc)", required=True)
    parser.add_argument("-o", "--output", help="Path for the output CSV file.", default="youtube_comments.csv")
    parser.add_argument("-k", "--api_key", help="Your YouTube Data API key. Overrides key in .env file.")
    parser.add_argument("-l", "--limit", type=int, help="Limit the number of comments to fetch (for testing).")
    parser.add_argument("-r", "--include_replies", action="store_true", help="Include replies to comments.")
    
    args = parser.parse_args()

    # --- API Key Handling ---
    api_key = args.api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("❌ YouTube API key not found. Please provide it via the --api_key argument or in a .env file.")
    else:
        youtube_service = initialize_youtube_api(api_key)
        if youtube_service:
            all_comments = scrape_comments(youtube_service, args.video_id, args.include_replies, args.limit)
            save_to_csv(all_comments, args.output)