import csv
from googleapiclient.discovery import build

# Replace with your actual API key
API_KEY = 'API KEY HERE'

# Replace with the video ID (not full URL, yt id is what comes after 'v=' in the URL)
VIDEO_ID = 'YP8mV_2RDLc'

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Function to get comments
def get_comments(video_id):
    comments = []
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            pageToken=next_page_token,
            maxResults=100,
            textFormat='plainText'
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return comments

# Fetch comments
print("🔄 Fetching comments...")
comments = get_comments(VIDEO_ID)

# Save to CSV
with open('youtube_comments.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(['Comment'])

    for comment in comments:
        text = comment.strip().replace('\n', ' ').replace('\r', '')
        if text:
            writer.writerow([text])

print("✅ Comments saved to 'youtube_comments.csv'")
