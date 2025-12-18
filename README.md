# Generate Gag Reel (Funny Clip Extractor)

An AI-powered application that takes a YouTube video URL, analyzes its transcript to identify humorous sections, and automatically stitches them together into a "gag reel".

## Features
- **Transcript Extraction**: Fetches transcripts from YouTube videos (standard or auto-generated).
- **AI Humor Analysis**: Uses Google's **Gemini AI** to read the transcript and intelligently pick out the funniest moments.
- **Auto-Editing**: Downloads the video and cuts/stitches the selected segments using `moviepy`.
- **Streamlit UI**: Simple, user-friendly web interface.

## Prerequisites
- **Python 3.8+**
- **Gemini API Key**: You can get one for free at [Google AI Studio](https://aistudio.google.com/).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/YOUR_USERNAME/generate-gag-reel.git
    cd generate-gag-reel
    ```

2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

    *Note: You may need to install [ImageMagick](https://imagemagick.org/index.php) if you encounter issues with MoviePy on some systems, though it is usually not required for basic cutting.*

## Usage

1.  Run the application:
    ```bash
    streamlit run app.py
    ```

2.  The app will open in your browser.
    - **Sidebar**: Enter your **Gemini API Key**.
    - **Main Input**: Paste the **YouTube URL**.
    - Click **Generate Gag Reel**.

3.  Wait for the process to complete (fetching, analyzing, downloading, editing). The final video will be displayed and available for download.

## Project Structure
- `app.py`: Main Streamlit application.
- `analysis_utils.py`: Logic for fetching transcripts and querying the LLM.
- `video_utils.py`: Logic for downloading videos (yt-dlp) and editing (moviepy).
- `requirements.txt`: Python dependencies.

## Disclaimer
This tool relies on the availability of YouTube transcripts. Videos without captions cannot be processed. Downloading copyrighted material may violate YouTube's Terms of Service; use responsibly and only for personal use or fair use.
