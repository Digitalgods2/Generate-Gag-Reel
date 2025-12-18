from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns a list of dictionaries with 'text', 'start', and 'duration'.
    """
    try:
        # v1.2.3+ uses instance-based API
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id)
        
        # Convert FetchedTranscriptSnippet objects to dicts
        result = []
        for snippet in transcript_data:
            result.append({
                'text': snippet.text,
                'start': snippet.start,
                'duration': getattr(snippet, 'duration', 0)
            })
        return result
        
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def analyze_humor(transcript, api_key, max_clip_seconds=15, max_clips=5):
    """
    Sends the transcript to Gemini to identify humorous sections.
    Returns a list of (start, end) tuples.
    """
    if not api_key:
        raise ValueError("API Key is required")
    
    # Create client with the new SDK
    client = genai.Client(api_key=api_key)

    # Prepare transcript for prompt
    formatted_transcript = ""
    for entry in transcript:
        start = entry['start']
        text = entry['text']
        formatted_transcript += f"[{start:.2f}] {text}\n"

    prompt = f"""
    You are an expert video editor and comedian. Your task is to analyze the following transcript of a YouTube video and identify the FUNNIEST sections to create a "gag reel".
    
    CRITICAL INSTRUCTION: You must return valid JSON only. Do not wrap it in markdown code blocks.
    The JSON should be a list of objects, where each object has a "start" and "end" timestamp (in seconds) representing a clip.
    Example: [{{"start": 10.5, "end": 20.0}}, {{"start": 45.0, "end": 60.0}}]
    
    CRITERIA:
    1. Focus ONLY on genuinely HUMOROUS content: jokes, punchlines, funny reactions, laughter, comedic timing, or absurd statements.
    2. Do NOT include general "interesting" or "engaging" content unless it is actually funny.
    3. Each clip should be {max_clip_seconds} seconds or less.
    4. Return EXACTLY {max_clips} clips - no more, no less. Pick only the BEST {max_clips}.
    5. Quality over quantity - be very selective.
    
    Here is the transcript:
    {formatted_transcript}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text_response = response.text.strip()
        
        # Cleanup if model adds markdown
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
        
        text_response = text_response.strip()
        
        # Try to parse as JSON first
        try:
            clips = json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback: use regex to extract timestamp pairs
            import re
            print(f"JSON parse failed, trying regex fallback...")
            pattern = r'"start"\s*:\s*([\d.]+)\s*,\s*"end"\s*:\s*([\d.]+)'
            matches = re.findall(pattern, text_response)
            if matches:
                clips = [{"start": float(m[0]), "end": float(m[1])} for m in matches]
            else:
                print(f"Regex fallback also failed")
                return []
        
        # Process clips to ensure they are valid tuples
        results = []
        for clip in clips:
            results.append((float(clip['start']), float(clip['end'])))
            
        return results

    except Exception as e:
        print(f"Error analyzing humor: {e}")
        # Return empty list on failure so the app doesn't crash
        return []

def analyze_quotes(transcript, api_key, max_clip_seconds=15, max_clips=5):
    """
    Sends the transcript to Gemini to identify memorable quotes.
    Returns a list of (start, end) tuples.
    """
    if not api_key:
        raise ValueError("API Key is required")
    
    # Create client with the new SDK
    client = genai.Client(api_key=api_key)

    # Prepare transcript for prompt
    formatted_transcript = ""
    for entry in transcript:
        start = entry['start']
        text = entry['text']
        formatted_transcript += f"[{start:.2f}] {text}\n"

    prompt = f"""
    You are an expert video editor specializing in creating highlight reels. Your task is to analyze the following transcript of a YouTube video and identify the most MEMORABLE and QUOTABLE moments.
    
    CRITICAL INSTRUCTION: You must return valid JSON only. Do not wrap it in markdown code blocks.
    The JSON should be a list of objects, where each object has a "start" and "end" timestamp (in seconds) representing a clip.
    Example: [{{"start": 10.5, "end": 20.0}}, {{"start": 45.0, "end": 60.0}}]
    
    QUALITY REQUIREMENTS:
    - Each quote MUST be a COMPLETE THOUGHT or idea - never cut off mid-sentence
    - Start the clip slightly before the quote begins so context is included
    - End the clip after the thought is fully expressed
    - Be EXTREMELY selective - only the absolute BEST quotes
    
    WHAT TO LOOK FOR (only pick the CREAM OF THE CROP):
    1. Profound statements - deep, meaningful insights about life, work, or relationships
    2. Good advice - practical wisdom that viewers could apply
    3. Clever observations - witty, smart, or insightful comments
    4. Weird or unique statements - unusual perspectives that stand out
    5. Special moments - emotional revelations, surprising admissions, or powerful declarations
    6. Quotable sound bites - memorable phrases that could go viral
    
    CONSTRAINTS:
    - Return EXACTLY {max_clips} clips - no more, no less
    - Pick ONLY the absolute BEST {max_clips} moments from the entire video
    - Each clip MUST be {max_clip_seconds} seconds or less
    - If a great quote would exceed {max_clip_seconds} seconds, trim it to the most essential part while keeping it complete
    - Prefer shorter, punchier quotes over long rambling sections
    
    Here is the transcript:
    {formatted_transcript}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text_response = response.text.strip()
        
        # Cleanup if model adds markdown
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
        
        text_response = text_response.strip()
        
        # Try to parse as JSON first
        try:
            clips = json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback: use regex to extract timestamp pairs
            import re
            print(f"JSON parse failed, trying regex fallback...")
            pattern = r'"start"\s*:\s*([\d.]+)\s*,\s*"end"\s*:\s*([\d.]+)'
            matches = re.findall(pattern, text_response)
            if matches:
                clips = [{"start": float(m[0]), "end": float(m[1])} for m in matches]
            else:
                print(f"Regex fallback also failed")
                return []
        
        # Process clips to ensure they are valid tuples
        results = []
        for clip in clips:
            results.append((float(clip['start']), float(clip['end'])))
            
        return results

    except Exception as e:
        print(f"Error analyzing quotes: {e}")
        return []

def parse_manual_transcript(text):
    """
    Parses a manually pasted transcript string into the expected format:
    [{'start': 0.0, 'text': 'words'}, ...]
    
    Supports:
    [00:12] Hello world
    0:12 Hello world
    00:12
    Hello world
    """
    import re
    
    # Regex to find timestamps: HH:MM:SS or MM:SS or M:SS
    # Captures timestamp in group 1
    timestamp_regex = r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?"
    
    lines = text.split('\n')
    entries = []
    
    current_entry = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = re.match(timestamp_regex, line)
        if match:
            # Found a line starting with a timestamp
            ts_str = match.group(1)
            parts = list(map(int, ts_str.split(':')))
            
            seconds = 0
            if len(parts) == 3: # HH:MM:SS
                seconds = parts[0]*3600 + parts[1]*60 + parts[2]
            elif len(parts) == 2: # MM:SS
                seconds = parts[0]*60 + parts[1]
                
            # Remove timestamp from text if it's on the same line
            # "00:12 Hello" -> "Hello"
            # "00:12" -> ""
            remaining_text = line[match.end():].strip()
            
            # If we had a previous entry, save it
            if current_entry and current_entry['text']:
                entries.append(current_entry)
            
            # Start new entry
            current_entry = {'start': float(seconds), 'text': remaining_text, 'duration': 0.0}
            
        else:
            # No timestamp, append to current entry text
            if current_entry:
                if current_entry['text']:
                    current_entry['text'] += " " + line
                else:
                    current_entry['text'] = line
                    
    # Append the last one
    if current_entry and current_entry['text']:
        entries.append(current_entry)
        
    return entries

