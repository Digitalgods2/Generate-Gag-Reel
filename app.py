import streamlit as st
import os
import re
from analysis_utils import get_transcript, analyze_humor
from video_utils import download_video, create_gag_reel

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    """
    # Regex for standard YouTube URLs and shortened youtu.be URLs
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def main():
    st.set_page_config(page_title="Funny Clip Extractor", page_icon="😂")
    
    st.title("😂 Funny Clip Extractor")
    st.markdown("Enter a YouTube URL below to automatically generate a gag reel of the funniest moments!")
    
    # Sidebar for API Configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Gemini API Key", type="password", help="Get a key from Google AI Studio")
        if not api_key:
            st.warning("Please enter your Gemini API Key to proceed.")
            
    # Main Input
    url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    
    if st.button("Generate Gag Reel", type="primary"):
        if not url:
            st.error("Please enter a YouTube URL.")
            return
        if not api_key:
            st.error("Please enter an API Key in the sidebar.")
            return
            
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL. Could not extract Video ID.")
            return
            
        # 1. Fetch Transcript
        with st.status("Fetching Transcript...", expanded=True) as status:
            transcript = get_transcript(video_id)
            if not transcript:
                status.update(label="No transcript found!", state="error")
                st.error("Could not retrieve a transcript for this video. Does it have captions?")
                return
            status.update(label="Transcript fetched request!", state="complete", expanded=False)
            
        # 2. Analyze Transcript
        with st.status("Finding funny moments (AI Analysis)...", expanded=True) as status:
            humorous_intervals = analyze_humor(transcript, api_key)
            if not humorous_intervals:
                status.update(label="No humor found.", state="error")
                st.warning("The AI could not find any humorous sections (or analysis failed).")
                return
            
            st.write("### Found Segments:")
            st.write(humorous_intervals)
            status.update(label=f"Found {len(humorous_intervals)} funny segments!", state="complete", expanded=False)

        # 3. Download Video
        with st.status("Downloading video...", expanded=True) as status:
            video_path = download_video(url)
            if not video_path:
                status.update(label="Download failed.", state="error")
                st.error("Failed to download video.")
                return
            status.update(label="Video downloaded!", state="complete", expanded=False)
            
        # 4. Create Gag Reel
        with st.status("Editing Gag Reel...", expanded=True) as status:
            output_file = create_gag_reel(video_path, humorous_intervals)
            if not output_file:
                status.update(label="Editing failed.", state="error")
                st.error("Failed to create gag reel.")
                return
            status.update(label="Gag Reel Ready!", state="complete", expanded=False)
            
        st.success("Done! Here is your gag reel:")
        st.video(output_file)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Gag Reel",
                data=file,
                file_name="gag_reel.mp4",
                mime="video/mp4"
            )

if __name__ == "__main__":
    main()
