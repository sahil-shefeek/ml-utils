# Reddit Comment Scraper

A simple and robust Python script to download all comments from any public Reddit post and save them as a structured CSV file. This tool is perfect for anyone looking to perform data analysis, archive discussions, or gather text data for projects.

The output CSV file includes the comment text, the author's username, the comment's score (upvotes), and a direct link to the comment.


## 📋 Prerequisites

Before you can use the script, you need two things:

1.  **Python 3**: If you don't have it, download it from [python.org](https://www.python.org/downloads/).

2.  **Reddit API Credentials**: You need to tell Reddit you're creating a script to get a unique `Client ID` and `Client Secret`. This is free and only takes a minute.

    **How to get Reddit API Credentials:**
    1.  Log in to your Reddit account.
    2.  Go to the Reddit [app preferences page](https://www.reddit.com/prefs/apps).
    3.  Scroll down and click the button that says **"are you a developer? create an app..."**.
    4.  Fill out the form:
        *   **name:** `comment-scraper` (or any name you like)
        *   **type:** Choose the **`script`** option.
        *   **redirect uri:** You can type `http://localhost:8080` in this box.
    5.  Click the **"create app"** button.
    6.  You will now see your newly created app.
        *   The long string of text under the name is your **`Client ID`**.
        *   The long string of text next to `secret` is your **`Client Secret`**.
    7.  Copy both of these down. You'll need them in the setup step.

## ⚙️ Installation & Setup

Follow these steps to get the script ready to run.

**1. Get the Code**

Download the script file (`scrape_reddit.py`) to a folder on your computer.

**2. Install Required Packages**

Open your terminal or command prompt and run this command to install the necessary Python libraries:

```bash
pip install praw python-dotenv tqdm
```

**3. Configure Your Credentials**

This is the most important step for making the script work.

1.  In the same folder where you saved the script, create a new file and name it exactly `.env`
2.  Open the `.env` file with a text editor and add the following lines. Paste your own credentials that you got from Reddit.

    ```
    # Your Reddit API Credentials
    REDDIT_CLIENT_ID="PASTE_YOUR_CLIENT_ID_HERE"
    REDDIT_CLIENT_SECRET="PASTE_YOUR_CLIENT_SECRET_HERE"
    REDDIT_USER_AGENT="Comment Scraper by u/YourUsername"
    ```

    *   Replace `PASTE_YOUR_CLIENT_ID_HERE` and `PASTE_YOUR_CLIENT_SECRET_HERE` with the credentials you copied.
    *   It's a good idea to replace `u/YourUsername` with your actual Reddit username.

## 🚀 How to Run the Script

You run the script from your terminal or command prompt. The only thing you *must* provide is the URL of the Reddit post you want to scrape.

---

### Basic Usage

This is the simplest way to run the script. It will scrape all comments from the post (sorted by "best") and save them to a file named `reddit_comments.csv`.

```bash
python scrape_reddit.py --url "https://www.reddit.com/r/AskReddit/comments/17u3q0g/what_is_a_green_flag_in_a_person/"
```

### Command-Line Options

You can control how the script works using these optional arguments:

| Argument               | Short | Description                                                   | Example                                                 |
| ---------------------- | ----- | ------------------------------------------------------------- | ------------------------------------------------------- |
| `--url <url>`          | `-u`  | **(Required)** The full URL of the Reddit post.               | `-u "https://..."`                                      |
| `--output <filename>`  | `-o`  | Set a custom name for the output CSV file.                    | `-o askreddit_comments.csv`                             |
| `--limit <number>`     | `-l`  | Stop after scraping a certain number of comments.             | `-l 100`                                                |
| `--sort <order>`       | `-s`  | Sort comments by `best`, `new`, `top`, `old`, `controversial`. | `-s new`                                                |

### Examples

**1. Scrape the 50 newest comments from a post:**

```bash
python scrape_reddit.py -u "URL_HERE" -l 50 -s new
```

**2. Scrape all controversial comments and save them to a specific file:**

```bash
python scrape_reddit.py -u "URL_HERE" -s controversial -o controversial_comments.csv
```

## 📄 Output File

The script will generate a CSV file that you can open with Excel, Google Sheets, or any spreadsheet program. It will have the following columns:

*   **Author**: The username of the person who made the comment.
*   **Comment**: The full text of the comment.
*   **Score**: The number of upvotes the comment has.
*   **ID**: The unique ID of the comment.
*   **Permalink**: A direct link to the comment on Reddit.

## ⚠️ Important Note

For Reddit posts with tens of thousands of comments, the initial step of "Flattening comment tree" can take a few minutes. Please be patient! The progress bar will appear as soon as the actual scraping begins.