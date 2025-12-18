# 🎬 Video Highlight Extractor

An AI-powered application that takes a YouTube video URL, analyzes its transcript, and automatically extracts the best moments into a highlight reel.

## Features

- **Two Extraction Modes:**
  - 😂 **Funny Moments** - Creates a gag reel of the funniest sections
  - 💬 **Memorable Quotes** - Extracts profound, clever, or quotable moments
- **Smart Transcript Handling**: Auto-fetches transcripts or accepts manual input
- **AI Analysis**: Uses Google's **Gemini AI** to intelligently identify the best moments
- **Auto-Editing**: Downloads video and cuts/stitches segments with black slugs between clips
- **Caching**: Re-run with different settings without re-downloading the video
- **Configurable Settings**:
  - Max clip length (5-60 seconds)
  - Max number of clips (3-20)
- **API Key Persistence**: Save your API key to `.env` for convenience

## Prerequisites

- **Python 3.8+**
- **Gemini API Key**: Free at [Google AI Studio](https://aistudio.google.com/)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/generate-gag-reel.git
   cd generate-gag-reel
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. In the sidebar:
   - Enter your **Gemini API Key**
   - Choose **Extraction Mode** (Funny Moments or Memorable Quotes)
   - Adjust **Clip Settings** as needed

3. Paste a **YouTube URL** and click **🎬 Generate Reel**

4. The final video will be displayed and available for download.

## Project Structure

- `app.py` - Main Streamlit application
- `analysis_utils.py` - Transcript fetching and AI analysis
- `video_utils.py` - Video downloading (yt-dlp) and editing (moviepy)
- `requirements.txt` - Python dependencies

## Disclaimer

This tool relies on YouTube transcripts. Videos without captions cannot be processed automatically. Downloading copyrighted material may violate YouTube's Terms of Service; use responsibly.
