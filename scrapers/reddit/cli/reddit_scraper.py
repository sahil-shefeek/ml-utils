import os
import csv
import praw
import argparse
from praw.exceptions import PRAWException
from dotenv import load_dotenv
from tqdm import tqdm

def initialize_reddit(client_id, client_secret, user_agent):
    """Initializes and returns a PRAW Reddit instance."""
    if not all([client_id, client_secret, user_agent]):
        print("❌ Missing one or more Reddit credentials. Check your .env file or arguments.")
        return None
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        # Test the connection by checking read_only status
        _ = reddit.read_only
        print("✅ Reddit API initialized successfully in read-only mode.")
        return reddit
    except PRAWException as e:
        print(f"❌ Error initializing PRAW: {e}")
        return None

def scrape_post_comments(reddit, post_url, sort_order='best', limit=None):
    """
    Scrapes comments from a Reddit post.

    Args:
        reddit: Initialized PRAW Reddit instance.
        post_url (str): The full URL of the Reddit post.
        sort_order (str): The order to sort comments by.
        limit (int, optional): Maximum number of comments to fetch.

    Returns:
        A list of dictionaries, where each dictionary represents a comment.
    """
    comments_data = []
    pbar = None
    try:
        submission = reddit.submission(url=post_url)
        print(f"▶️ Fetching post: '{submission.title}'")

        # Set the comment sort order
        submission.comment_sort = sort_order
        
        # Flatten the comment tree to get all comments, including replies
        # replace_more(limit=None) fetches all, limit=0 is a fast way to process top-level
        print("🔄 Flattening comment tree (this may take a while for large posts)...")
        submission.comments.replace_more(limit=None)
        
        comment_queue = submission.comments.list()
        
        # Set up progress bar
        pbar = tqdm(total=limit or len(comment_queue), desc="Scraping Comments")
        
        for comment in comment_queue:
            # Skip if it's a "MoreComments" object, though list() should handle this.
            if isinstance(comment, praw.models.MoreComments):
                continue

            comments_data.append({
                'Author': comment.author.name if comment.author else '[deleted]',
                'Comment': comment.body.strip().replace('\n', ' ').replace('\r', ''),
                'Score': comment.score,
                'ID': comment.id,
                'Permalink': f"https://www.reddit.com{comment.permalink}"
            })
            pbar.update(1)

            if limit and len(comments_data) >= limit:
                print(f"\n✅ Reached comment limit of {limit}.")
                break
                
    except PRAWException as e:
        print(f"\n❌ A PRAW error occurred: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        if pbar:
            pbar.close()

    return comments_data

def save_to_csv(comments, output_path):
    """Saves a list of comment dictionaries to a CSV file."""
    if not comments:
        print("ℹ️ No comments were scraped to save.")
        return

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['Author', 'Comment', 'Score', 'ID', 'Permalink']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comments)
        print(f"✅ Successfully saved {len(comments)} comments to '{output_path}'")
    except IOError as e:
        print(f"❌ Error saving file: {e}")

if __name__ == '__main__':
    load_dotenv()

    parser = argparse.ArgumentParser(description="Scrape comments from a Reddit post and save to a CSV file.")
    
    parser.add_argument("-u", "--url", help="Full URL of the Reddit post to scrape", required=True)
    parser.add_argument("-o", "--output", help="Path for the output CSV file.", default="reddit_comments.csv")
    parser.add_argument("-l", "--limit", type=int, help="Limit the number of comments to fetch.")
    parser.add_argument(
        "-s", "--sort", 
        choices=['best', 'top', 'new', 'old', 'controversial', 'q&a'], 
        default='best', 
        help="Sort order for comments."
    )
    
    args = parser.parse_args()

    # --- Credential Handling ---
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    reddit_instance = initialize_reddit(client_id, client_secret, user_agent)
    
    if reddit_instance:
        all_comments = scrape_post_comments(reddit_instance, args.url, args.sort, args.limit)
        save_to_csv(all_comments, args.output)