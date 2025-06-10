# YouTube Comment Scraper

A simple yet powerful Python script to scrape all public comments from a YouTube video and save them into a clean, structured CSV file. This tool is designed to be easy to use, robust, and respectful of the YouTube API's limitations.

The output CSV contains the comment text, author, publication date, and like count, making it perfect for data analysis, sentiment analysis, or archiving discussions.


## 📋 Prerequisites

Before you begin, you will need two things:

1.  **Python 3**: If you don't have Python installed, you can download it from [python.org](https://www.python.org/downloads/).

2.  **YouTube Data API v3 Key**: This is a free key from Google that allows you to access YouTube's data.

    **How to get an API Key:**
    1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
    2.  Create a new project (or select an existing one).
    3.  In the navigation menu, go to **APIs & Services > Library**.
    4.  Search for **"YouTube Data API v3"** and click on it.
    5.  Click the **Enable** button.
    6.  Once enabled, go to **APIs & Services > Credentials**.
    7.  Click **+ CREATE CREDENTIALS** at the top and select **API key**.
    8.  Your key will be created. **Copy this key** and keep it safe.

## ⚙️ Installation & Setup

Follow these steps to get the script ready to run.

**1. Clone or Download the Code**

If you have Git, clone the repository. Otherwise, you can download the script and files as a ZIP.

```bash
git clone <repository-url>
cd <repository-folder>
```

**2. Install Required Packages**

This script requires a few Python packages. You can install them all with this single command:

```bash
pip install google-api-python-client python-dotenv tqdm
```

**3. Configure Your API Key**

To keep your API key secure, we will store it in a local environment file.

1.  In the project folder, create a new file named `.env`
2.  Open the `.env` file with a text editor and add the following line, pasting your own API key in place of `YOUR_API_KEY_HERE`:

    ```
    YOUTUBE_API_KEY="YOUR_API_KEY_HERE"
    ```

    Make sure to save the file. The script will automatically read this key.

## 🚀 How to Run the Script

You run the script from your terminal or command prompt. The only required argument is the YouTube video ID.

#### How to Find a Video ID?

The video ID is the unique code found in the YouTube URL after `v=`.

For example, in the URL `https://www.youtube.com/watch?v=dQw4w9WgXcQ`, the video ID is `dQw4w9WgXcQ`.

---

### Basic Usage

This will scrape all top-level comments from the video and save them to `youtube_comments.csv`.

```bash
python scrape_youtube.py --video_id dQw4w9WgXcQ
```

### Command-Line Options

You can customize the script's behavior using the following optional arguments:

| Argument               | Short | Description                                                   | Example                                            |
| ---------------------- | ----- | ------------------------------------------------------------- | -------------------------------------------------- |
| `--output <filename>`  | `-o`  | Specify a custom name for the output CSV file.                | `-o my_video_comments.csv`                         |
| `--limit <number>`     | `-l`  | Stop after scraping a specific number of comments.            | `-l 100`                                           |
| `--include_replies`    | `-r`  | Include replies in the scrape. (This is a flag, no value needed). | `-r`                                               |
| `--api_key <key>`      | `-k`  | Use a specific API key (overrides the one in `.env`).         | `-k "AIzaSy..."`                                   |
| `--video_id <id>`      | `-v`  | **(Required)** The ID of the YouTube video to scrape.         | `-v dQw4w9WgXcQ`                                   |

### Examples

**1. Scrape comments and include replies:**

```bash
python scrape_youtube.py -v dQw4w9WgXcQ -r
```

**2. Scrape the first 50 comments and save to a custom file:**

```bash
python scrape_youtube.py -v dQw4w9WgXcQ -l 50 -o test_comments.csv
```

**3. Scrape a different video, including replies:**

```bash
python scrape_youtube.py --video_id YP8mV_2RDLc --include_replies
```

## 📄 Output File

The script will produce a CSV file with the following columns:

*   **Author**: The display name of the user who posted the comment.
*   **Comment**: The full text of the comment.
*   **Timestamp**: The date and time the comment was published (in UTC).
*   **Likes**: The number of likes the comment has received.

## ⚠️ Important Note on API Quotas

The YouTube Data API has a daily usage limit (a "quota"). Each request the script makes (typically fetching 100 comments at a time) consumes a small part of your quota.

*   Scraping videos with hundreds of thousands of comments may exhaust your daily quota.
*   If you hit the limit, the script will stop gracefully and save all comments it has collected up to that point. The error message will say `QUOTA EXCEEDED`.
*   To conserve your quota during testing, always use the `--limit` or `-l` flag.