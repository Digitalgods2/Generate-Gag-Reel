import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os

def get_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns a list of dictionaries with 'text', 'start', and 'duration'.
    """
    try:
        # List of languages to attempt: Manual English, Auto-generated English
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find a manual or auto-generated transcript in English
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
             # If no English, try to translate or just take the first available one?
             # For now, let's just grab the generated one or fallback
             transcript = transcript_list.find_generated_transcript(['en'])
        
        return transcript.fetch()
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def analyze_humor(transcript, api_key):
    """
    Sends the transcript to Gemini to identify humorous sections.
    Returns a list of (start, end) tuples.
    """
    if not api_key:
        raise ValueError("API Key is required")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare transcript for prompt
    # Chunking might be necessary for very long videos, but for now let's try fitting it all.
    # We will simply format it as time-stamped text.
    
    formatted_transcript = ""
    for entry in transcript:
        start = entry['start']
        text = entry['text']
        formatted_transcript += f"[{start:.2f}] {text}\n"

    prompt = f"""
    You are an expert video editor and comedian. Your task is to analyze the following transcript of a YouTube video and identify the funniest or most humorous sections to create a "gag reel".
    
    CRITICAL INSTRUCTION: You must return valid JSON only. Do not wrap it in markdown code blocks.
    The JSON should be a list of objects, where each object has a "start" and "end" timestamp (in seconds) representing a clip.
    Example: [{{"start": 10.5, "end": 20.0}}, {{"start": 45.0, "end": 60.0}}]
    
    Select only the absolute best parts. Keep clips concise (5-30 seconds ideally).
    If you can't find anything explicitly funny, find the most engaging or high-energy moments.
    
    Here is the transcript:
    {formatted_transcript}
    """

    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Cleanup if model adds markdown
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        clips = json.loads(text_response)
        
        # Process clips to ensure they are valid tuples
        results = []
        for clip in clips:
            results.append((float(clip['start']), float(clip['end'])))
            
        return results

    except Exception as e:
        print(f"Error analyzing humor: {e}")
        # Return empty list on failure so the app doesn't crash
        return []
