import yt_dlp
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os

def download_video(url, output_path="downloaded_video.mp4"):
    """
    Downloads a YouTube video using yt-dlp.
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    # Remove existing file if it exists to avoid conflicts
    if os.path.exists(output_path):
        os.remove(output_path)
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def create_gag_reel(video_path, intervals, output_path="gag_reel.mp4"):
    """
    Cuts the video at the specified intervals and stitches them together.
    intervals: list of tuples (start, end)
    """
    try:
        # Load the original video
        original_clip = VideoFileClip(video_path)
        
        clips = []
        for start, end in intervals:
            # Ensure start/end are within bounds and valid
            if start < 0: start = 0
            if end > original_clip.duration: end = original_clip.duration
            if start >= end: continue
            
            # Create subclip
            clip = original_clip.subclip(start, end)
            clips.append(clip)
            
        if not clips:
            print("No valid clips were created.")
            return None
            
        # Concatenate clips
        final_clip = concatenate_videoclips(clips)
        
        # Write the result to a file
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)
        
        # Close clips to release resources
        original_clip.close()
        # final_clip.close() # Sometimes fails if close is called too early?
        
        return output_path
        
    except Exception as e:
        print(f"Error creating gag reel: {e}")
        return None
