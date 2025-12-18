import streamlit as st
import os
import re
from dotenv import load_dotenv
from analysis_utils import get_transcript, analyze_humor, analyze_quotes
from video_utils import download_video, create_gag_reel

# Load env vars
load_dotenv()

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
    
    # Initialize session state for caching
    if 'cached_url' not in st.session_state:
        st.session_state.cached_url = None
    if 'cached_transcript_text' not in st.session_state:
        st.session_state.cached_transcript_text = None
    if 'cached_video_path' not in st.session_state:
        st.session_state.cached_video_path = None
    if 'cached_transcript' not in st.session_state:
        st.session_state.cached_transcript = None
    
    st.title("🎬 Video Highlight Extractor")
    st.markdown("Enter a YouTube URL below to automatically extract the best moments!")
    
    # Sidebar for API Configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Try to load from env
        default_key = os.getenv("GEMINI_API_KEY", "")
        api_key = st.text_input("Gemini API Key", value=default_key, type="password", help="Get a key from Google AI Studio")
        
        if st.button("Save API Key to .env"):
            if api_key:
                with open(".env", "w") as f:
                    f.write(f"GEMINI_API_KEY={api_key}")
                st.success("Key saved to .env!")
                os.environ["GEMINI_API_KEY"] = api_key # Update current session too
            else:
                st.error("Please enter a key to save.")
                
        if not api_key:
            st.warning("Please enter your Gemini API Key to proceed.")
        
        st.divider()
        st.subheader("Extraction Mode")
        extraction_mode = st.radio("What to extract:", ["😂 Funny Moments", "💬 Memorable Quotes"], index=0)
        
        st.divider()
        st.subheader("Clip Settings")
        max_clip_seconds = st.slider("Max Clip Length (seconds)", min_value=5, max_value=60, value=15, step=5)
        max_clips = st.slider("Max Number of Clips", min_value=3, max_value=20, value=5, step=1)
    
    # Initialize input session state
    if 'url_input' not in st.session_state:
        st.session_state.url_input = ""
    if 'transcript_input' not in st.session_state:
        st.session_state.transcript_input = ""
            
    # Main Input with Clear button
    st.markdown("### YouTube Video URL")
    url_col1, url_col2 = st.columns([6, 1])
    with url_col1:
        url = st.text_input("URL", value=st.session_state.url_input, placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
        st.session_state.url_input = url
    with url_col2:
        if st.button("🗑️ Clear", key="clear_url"):
            st.session_state.url_input = ""
            st.session_state.cached_url = None
            st.session_state.cached_video_path = None
            st.session_state.cached_transcript = None
            st.rerun()
    
    # Manual Transcript Input (always visible)
    st.markdown("### Manual Transcript (Optional)")
    st.caption("Paste here if auto-fetch fails. Must include timestamps (e.g., '0:05 text...')")
    trans_col1, trans_col2 = st.columns([6, 1])
    with trans_col1:
        manual_transcript_text = st.text_area("Transcript", value=st.session_state.transcript_input, height=150, label_visibility="collapsed")
        st.session_state.transcript_input = manual_transcript_text
    with trans_col2:
        if st.button("🗑️ Clear", key="clear_transcript"):
            st.session_state.transcript_input = ""
            st.session_state.cached_transcript_text = None
            st.session_state.cached_transcript = None
            st.rerun()

    # Check if we need to re-download/re-fetch
    url_changed = (url != st.session_state.cached_url)
    transcript_changed = (manual_transcript_text != st.session_state.cached_transcript_text)
    needs_new_source = url_changed or transcript_changed
    
    # Show cache status
    if st.session_state.cached_video_path and os.path.exists(st.session_state.cached_video_path) and not needs_new_source:
        st.info("📦 Using cached video. Change URL or transcript to download a new one.")

    if st.button("🎬 Generate Reel", type="primary"):
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
            
        # 1. Fetch Transcript (or parse manual) - use cache if available
        transcript = None
        
        if needs_new_source or st.session_state.cached_transcript is None:
            if manual_transcript_text:
                from analysis_utils import parse_manual_transcript
                with st.status("Parsing manual transcript...", state="running", expanded=True) as status:
                    transcript = parse_manual_transcript(manual_transcript_text)
                    if not transcript:
                         status.update(label="Invalid format", state="error")
                         st.error("Could not parse timestamps from your text. Please use format like '0:05 Hello'.")
                         return
                    status.update(label="Manual transcript parsed!", state="complete", expanded=False)
            else:
                with st.status("Fetching Transcript...", state="running", expanded=True) as status:
                    transcript = get_transcript(video_id)
                    if not transcript:
                        status.update(label="No transcript found!", state="error")
                        st.error("Could not retrieve a transcript. Try pasting one manually in the 'Manual Transcript' box above.")
                        return
                    status.update(label="Transcript fetched!", state="complete", expanded=False)
            
            # Cache the transcript
            st.session_state.cached_transcript = transcript
            st.session_state.cached_url = url
            st.session_state.cached_transcript_text = manual_transcript_text
        else:
            transcript = st.session_state.cached_transcript
            st.success("Using cached transcript.")
            
        # 2. Analyze Transcript (always re-run since clip length or mode may change)
        intervals = None
        if extraction_mode == "😂 Funny Moments":
            with st.status("Finding funny moments (AI Analysis)...", expanded=True) as status:
                intervals = analyze_humor(transcript, api_key, max_clip_seconds=max_clip_seconds, max_clips=max_clips)
                if not intervals:
                    status.update(label="No humor found.", state="error")
                    st.warning("The AI could not find any humorous sections (or analysis failed).")
                    return
                status.update(label=f"Found {len(intervals)} funny segments!", state="complete", expanded=False)
        else:
            with st.status("Finding memorable quotes (AI Analysis)...", expanded=True) as status:
                intervals = analyze_quotes(transcript, api_key, max_clip_seconds=max_clip_seconds, max_clips=max_clips)
                if not intervals:
                    status.update(label="No quotes found.", state="error")
                    st.warning("The AI could not find any memorable quotes (or analysis failed).")
                    return
                status.update(label=f"Found {len(intervals)} memorable quotes!", state="complete", expanded=False)
        
        # Display found segments nicely
        st.write("### Found Segments:")
        for i, (start, end) in enumerate(intervals, 1):
            st.write(f"Clip {i}: {end-start:.1f}s")

        # 3. Download Video - use cache if available and source hasn't changed
        video_path = None
        if needs_new_source or st.session_state.cached_video_path is None or not os.path.exists(st.session_state.cached_video_path):
            with st.status("Downloading video...", expanded=True) as status:
                video_path = download_video(url)
                if not video_path:
                    status.update(label="Download failed.", state="error")
                    st.error("Failed to download video.")
                    return
                status.update(label="Video downloaded!", state="complete", expanded=False)
                
                # Cache the video path
                st.session_state.cached_video_path = video_path
        else:
            video_path = st.session_state.cached_video_path
            st.success("Using cached video download.")
            
        # 4. Create Highlight Reel
        reel_type = "Gag Reel" if extraction_mode == "😂 Funny Moments" else "Quote Reel"
        with st.status(f"Editing {reel_type}...", expanded=True) as status:
            output_file = create_gag_reel(video_path, intervals)
            if not output_file:
                status.update(label="Editing failed.", state="error")
                st.error("Failed to create highlight reel.")
                return
            status.update(label=f"{reel_type} Ready!", state="complete", expanded=False)
            
        st.success(f"Done! Here is your {reel_type.lower()}:")
        st.video(output_file)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label=f"Download {reel_type}",
                data=file,
                file_name=f"{reel_type.lower().replace(' ', '_')}.mp4",
                mime="video/mp4"
            )

if __name__ == "__main__":
    main()

