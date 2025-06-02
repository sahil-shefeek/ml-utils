import praw
import csv

# Initialize Reddit client
reddit = praw.Reddit(
    client_id="JNleeXXJjdQIkQKkHuJtBA",
    client_secret="jqJN1f5MWP9nhbwuRqhuVremduVBTg",
    user_agent="personal use script by shibu"
)

# Reddit post URL
post_url = "https://www.reddit.com/r/programming/comments/eodr2f/the_no_code_delusion/"

# Load the submission
submission = reddit.submission(url=post_url)

# Flatten the comment tree
submission.comments.replace_more(limit=None)

# Prepare CSV file
with open("reddit_comments.csv", mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(["Comment"])

    for comment in submission.comments.list():
        text = comment.body.strip().replace('\n', ' ').replace('\r', '')
        if text:  # Skip empty comments
            writer.writerow([text])

print("✅ Comments saved to 'reddit_comments.csv'")
