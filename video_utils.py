import yt_dlp
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip
import os
import uuid
import glob

def cleanup_old_files():
    """
    Removes old downloaded videos and gag reels to prevent clutter.
    """
    patterns = ["downloaded_video_*.mp4", "gag_reel_*.mp4", "*.part", "*.f137.mp4", "*.f140.m4a"]
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except:
                pass  # Ignore if file is locked

def download_video(url):
    """
    Downloads a YouTube video using yt-dlp with a unique filename.
    """
    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    output_path = f"downloaded_video_{unique_id}.mp4"
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    
    # Clean up old files first
    cleanup_old_files()
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def create_gag_reel(video_path, intervals, slug_duration=2.0):
    """
    Cuts the video at the specified intervals and stitches them together.
    Adds a black slug between each clip for easier editing.
    intervals: list of tuples (start, end)
    slug_duration: duration of black slug in seconds
    """
    # Generate unique output filename
    unique_id = uuid.uuid4().hex[:8]
    output_path = f"gag_reel_{unique_id}.mp4"
    
    original_clip = None
    final_clip = None
    
    try:
        # Load the original video
        original_clip = VideoFileClip(video_path)
        
        # Get video properties for the black slug
        video_size = original_clip.size
        video_fps = original_clip.fps
        
        # Create a black slug clip
        black_slug = ColorClip(size=video_size, color=(0, 0, 0), duration=slug_duration)
        black_slug = black_slug.set_fps(video_fps)
        
        clips_with_slugs = []
        for i, (start, end) in enumerate(intervals):
            # Ensure start/end are within bounds and valid
            if start < 0: start = 0
            
            # Add 2 seconds buffer to the end to capture punchlines
            end = end + 2.0
            
            if end > original_clip.duration: end = original_clip.duration
            if start >= end: continue
            
            # Create subclip
            clip = original_clip.subclip(start, end)
            clips_with_slugs.append(clip)
            
            # Add a black slug after each clip (except the last one)
            if i < len(intervals) - 1:
                clips_with_slugs.append(black_slug)
            
        if not clips_with_slugs:
            print("No valid clips were created.")
            if original_clip:
                original_clip.close()
            return None
            
        # Concatenate clips with slugs
        final_clip = concatenate_videoclips(clips_with_slugs)
        
        # Write the result to a file
        temp_audio = f"temp-audio_{unique_id}.m4a"
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True)
        
        return output_path
        
    except Exception as e:
        print(f"Error creating gag reel: {e}")
        return None
    finally:
        # Ensure clips are closed to release file handles
        if original_clip:
            try:
                original_clip.close()
            except:
                pass
        if final_clip:
            try:
                final_clip.close()
            except:
                pass
