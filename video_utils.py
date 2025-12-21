import yt_dlp
from moviepy.editor import VideoFileClip, concatenate_videoclips, ColorClip
import os
import uuid
import glob

# Buffer constants (in seconds) - used for clip extraction
PRE_ROLL_BUFFER = 0.5   # Added before clip start to catch first syllable
POST_ROLL_BUFFER = 2.0  # Added after clip end for punchline/reaction

def cleanup_old_files():
    """
    Removes old downloaded videos, gag reels, and preview clips to prevent clutter.
    """
    patterns = [
        "downloaded_video_*.mp4", 
        "gag_reel_*.mp4", 
        "preview_clip_*.mp4",
        "*.part", 
        "*.f137.mp4", 
        "*.f140.m4a",
        "temp-*.m4a",
        "temp-preview-*.m4a"
    ]
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
            
            # Add buffers for context
            start = max(0, start - PRE_ROLL_BUFFER)
            end = end + POST_ROLL_BUFFER
            
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

def create_single_clip(video_path, start, end, index):
    """
    Creates a single clip from the video for preview purposes using FFmpeg.
    This is much faster than MoviePy for long videos as it seeks directly.
    Returns the path to the preview clip.
    """
    import subprocess
    
    unique_id = uuid.uuid4().hex[:8]
    output_path = f"preview_clip_{index}_{unique_id}.mp4"
    
    try:
        # Add buffers for context
        start = max(0, start - PRE_ROLL_BUFFER)
        buffered_end = end + POST_ROLL_BUFFER
        duration = buffered_end - start
        
        # Use FFmpeg directly for fast seeking and extraction
        # -ss before -i enables fast seeking
        # -t specifies duration
        # -c:v libx264 -preset ultrafast for fast encoding
        # -c:a aac for audio
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-ss', str(start),  # Seek to start (before -i for fast seek)
            '-i', video_path,
            '-t', str(duration),  # Duration of clip
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',  # Lower quality for faster preview
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'error',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"FFmpeg error for clip {index}: {result.stderr}")
            return None
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            print(f"Preview clip {index} was not created or is empty")
            return None
        
    except subprocess.TimeoutExpired:
        print(f"Timeout creating preview clip {index}")
        return None
    except FileNotFoundError:
        print(f"FFmpeg not found. Please install FFmpeg and add it to PATH.")
        # Fallback to MoviePy if FFmpeg is not available
        return create_single_clip_moviepy(video_path, start, end, index)
    except Exception as e:
        print(f"Error creating preview clip {index}: {e}")
        return None


def create_single_clip_moviepy(video_path, start, end, index):
    """
    Fallback: Creates a single clip using MoviePy (slower but works without FFmpeg).
    """
    unique_id = uuid.uuid4().hex[:8]
    output_path = f"preview_clip_{index}_{unique_id}.mp4"
    
    original_clip = None
    subclip = None
    
    try:
        original_clip = VideoFileClip(video_path)
        
        # Add buffers for context (same as FFmpeg version)
        start = max(0, start - PRE_ROLL_BUFFER)
        buffered_end = end + POST_ROLL_BUFFER
        if buffered_end > original_clip.duration:
            buffered_end = original_clip.duration
        if start >= buffered_end:
            return None
        
        subclip = original_clip.subclip(start, buffered_end)
        
        # Write preview clip (lower quality for speed)
        temp_audio = f"temp-preview-audio_{unique_id}.m4a"
        subclip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile=temp_audio,
            remove_temp=True,
            preset="ultrafast",  # Fast encoding for preview
            verbose=False,
            logger=None
        )
        
        return output_path
        
    except Exception as e:
        print(f"Error creating preview clip {index} (MoviePy fallback): {e}")
        return None
    finally:
        if subclip:
            try:
                subclip.close()
            except:
                pass
        if original_clip:
            try:
                original_clip.close()
            except:
                pass
