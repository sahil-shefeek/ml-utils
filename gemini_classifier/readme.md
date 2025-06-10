# Gemini Sentiment Analysis for Label Studio

This script automates the process of sentiment analysis on a CSV file of user comments using the Google Gemini API. It is designed to handle large datasets efficiently by processing comments in batches, respecting API rate limits, and generating a pre-annotation file specifically formatted for easy import into Label Studio.

The key feature of this tool is its resilience. It can be safely interrupted (`Ctrl+C`) and will save its progress. It can then be restarted to automatically resume from where it left off, preventing duplicate processing and wasted API calls.

## Features

*   **Sentiment Analysis with Gemini:** Leverages the power of Google's Gemini models (e.g., `gemini-1.5-flash-latest`) to classify text into `positive`, `negative`, or `neutral` categories.
*   **Label Studio Integration:** Outputs a JSON file in the correct format for Label Studio's pre-annotation system, allowing you to immediately start reviewing, rather than labeling from scratch.
*   **Built-in Rate Limiting:** Automatically waits between API calls to respect the standard 10 Requests Per Minute (RPM) limit of the Gemini API.
*   **Graceful Shutdown & Progress Saving:** If the script is stopped for any reason (e.g., `Ctrl+C`, an unexpected error), it automatically saves all the work completed so far.
*   **Automatic Resumption:** Before starting, the script checks the output file for previously analyzed comments and skips them, ensuring it only processes new data.
*   **Targeted Processing:** Use command-line arguments to process specific slices of your data (e.g., rows 1000 to 2000), making large jobs manageable.

## Requirements

You will need Python 3.7+ and the following libraries:

*   `google-generativeai`
*   `pandas`
*   `python-dotenv`
*   `tqdm`

You can install them all at once using pip:
```bash
pip install google-generativeai pandas python-dotenv tqdm
```

## Setup

1.  **Save the Script:** Save the code as a Python file (e.g., `analyze_sentiments.py`).

2.  **Prepare your Data:** You need a CSV file containing the comments you want to analyze. The script requires a column named `Comment` by default.

3.  **Set Up API Key:** Your Google Gemini API key is required. It's recommended to use a `.env` file for security.
    *   Create a file named `.env` in the same directory as your script.
    *   Add your API key and optionally specify a model name to this file. It should look like this:

    ```.env
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    GEMINI_MODEL_NAME="gemini-1.5-flash-latest"
    ```
    The script will automatically load these variables.

## Usage

The script is run from the command line and accepts several arguments to control its behavior.

### Command-Line Arguments

*   `-i` or `--input_csv`: **(Required)** Path to the input CSV file.
*   `-o` or `--output_json`: **(Required)** Path for the output Label Studio JSON file.
*   `-b` or `--batch_size`: Number of comments to process in each API call (default: 10).
*   `-k` or `--api_key`: Your Gemini API key. If not provided, it will be read from the `.env` file or you will be prompted to enter it.
*   `-m` or `--model_name`: The Gemini model to use. Defaults to what's in `.env` or `gemini-1.5-flash-latest`.
*   `-l` or `--limit`: Restricts processing to a specific number of *new* comments. Useful for quick tests.
*   `--start-from`: The starting row index from the CSV to begin processing.
*   `--end-at`: The ending row index (exclusive) from the CSV to stop processing.

### Examples

**1. Basic First-Time Run**
This command will process all comments in `reddit_comments.csv` and save the results to `pre-annotations.json`.

```bash
python analyze_sentiments.py -i reddit_comments.csv -o pre-annotations.json
```

**2. Resuming an Interrupted Job**
If the previous command was stopped, simply run it again. The script will load `pre-annotations.json`, check which comments have already been processed, and automatically resume with the remaining ones.

```bash
python analyze_sentiments.py -i reddit_comments.csv -o pre-annotations.json
```

**3. Processing a Specific Slice of the Dataset**
This is useful for breaking a very large file into smaller chunks. This example processes rows 500 through 999.

```bash
python analyze_sentiments.py -i large_dataset.csv -o annotations_part_2.json --start-from 500 --end-at 1000
```

**4. Running a Quick Test on the First 50 Comments**
Use the `--limit` flag to only process the first 50 new comments.

```bash
python analyze_sentiments.py -i reddit_comments.csv -o test_annotations.json --limit 50
```

**5. Using a Different Model and Batch Size**
This command uses the `gemini-1.5-pro-latest` model with a larger batch size. Note that larger batches may take longer per API call.

```bash
python analyze_sentiments.py -i reddit_comments.csv -o pro_annotations.json --model_name "gemini-1.5-pro-latest" --batch_size 25
```

## Label Studio Integration

1.  **Import Data:** In your Label Studio project, click the "Import" button and upload the `output.json` file generated by the script.

2.  **Configure Labeling Interface:** For the pre-annotations to appear, your labeling interface must be configured to match the data. Go to **Settings > Labeling Interface**.
    *   Click "Code" and paste the following XML configuration.
    *   **Crucially**, the `value` attributes (`positive`, `negative`, `neutral`) are lowercase to match the script's output.

    ```xml
    <View>
      <Text name="text" value="$text"/>
      <View style="box-shadow: 2px 2px 5px #999; padding: 20px; margin-top: 2em; border-radius: 5px;">
        <Header value="Choose text sentiment"/>
        <Choices name="sentiment" toName="text" choice="single" showInLine="true">
          <Choice value="positive"/>
          <Choice value="negative"/>
          <Choice value="neutral"/>
        </Choices>
      </View>
    </View>
    ```

3.  **Show Predictions to Annotators:** In **Settings > Labeling Interface > General**, make sure the **"Show predictions to annotators"** toggle is enabled.

Once configured, when you start labeling, the sentiment predicted by the Gemini model will be pre-selected, allowing your annotators to simply validate or correct it.