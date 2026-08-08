import os
import requests
import json
import urllib.parse
import time
import random
import textwrap
import asyncio
import base64
import edge_tts
from PIL import Image, ImageDraw, ImageFont

# MoviePy for Long Video Assembly
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, 
    concatenate_audioclips, concatenate_videoclips
)
from moviepy.audio.fx.all import volumex

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_url(b64_string):
    return base64.b64decode(b64_string).decode("utf-8")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_font():
    font_path = "BoldFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading Font...")
        url = get_url("aHR0cHM6Ly9naXRodWIuY29tL2dvb2dsZS9mb250cy9yYXcvbWFpbi9vZmwvbW9udHNlcnJhdC9Nb250c2VycmF0LUJsYWNrLnR0Zg==")
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(font_path, 'wb') as f: 
                f.write(res.content)
    return font_path if os.path.exists(font_path) else None

def download_background_music():
    print("🎵 Downloading Long Ambient Audio...")
    music_url = get_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8wMy8xNS9hdWRpb181MTE2ZmMwMWMxLm1wMz9maWxlbmFtZT1kYXJrLWFtYmllbnQtMTA3Nzc0Lm1wMw==")
    music_path = "ambient_bg.mp3"
    try:
        res = requests.get(music_url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(res.content)
    except Exception as e:
        print(f"⚠️ Background music skipped: {e}")
    return music_path if os.path.exists(music_path) else None

def get_active_gemini_model():
    """Automatically discover working Gemini model from Google API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            for preferred in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash-latest"]:
                if preferred in models:
                    return preferred
            if models:
                return models[0]
    except Exception as e:
        print(f"⚠️ Could not fetch dynamic model list: {e}")
    return "gemini-2.5-flash"

def call_gemini(prompt):
    active_model = get_active_gemini_model()
    print(f"🤖 Using Gemini Model: {active_model}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.85}
    }

    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    data = res.json()

    if res.status_code == 200 and 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text'].strip()
    else:
        error_msg = data.get('error', {}).get('message', 'Unknown Error')
        raise Exception(f"❌ Gemini API Error ({res.status_code}): {error_msg}")

def generate_dark_canvas_image(title_text, filename="background.png"):
    print("🎨 Creating Dark Aesthetic Artwork Canvas...")
    w, h = 1920, 1080
    img = Image.new('RGB', (w, h), color=(12, 12, 18))
    draw = ImageDraw.Draw(img)

    font_path = download_font()
    try:
        font = ImageFont.truetype(font_path, 60)
    except:
        font = ImageFont.load_default()

    wrapped_lines = textwrap.wrap(title_text, width=42)
    total_h = len(wrapped_lines) * 75
    y = (h - total_h) // 2

    for line in wrapped_lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = font.getlength(line)
        x = (w - line_w) // 2
        draw.text((x, y), line, font=font, fill=(240, 240, 240), stroke_width=3, stroke_fill=(0, 0, 0))
        y += 75

    img.save(filename)
    return filename

def generate_long_audiobook_script():
    print("🧠 Outlining Long 20-50 Minute Story via Gemini API...")
    
    genres = ["Mystery Horror Thriller", "Dark Psychology Secrets", "Historical Secret Files", "Psychological Crime Thriller"]
    selected_genre = random.choice(genres)

    outline_prompt = f"""
    You are a viral YouTube Audiobook Creator. Create an outline for a long 20-30 minute Hindi/Hinglish story in '{selected_genre}'.
    Divide the story into 5 sequential Chapters.
    Output JSON ONLY:
    {{
      "metadata": {{
        "title": "Unsolved Mystery - Hindi Full Audiobook Story",
        "description": "Listen to this long gripping audiobook story in Hindi. #audiobook #hindi #story #mystery",
        "tags": ["audiobook", "hindi story", "thriller", "full story"]
      }},
      "chapters": [
        {{"chapter_num": 1, "topic": "The Strange Discovery"}},
        {{"chapter_num": 2, "topic": "The Unseen Shadows"}},
        {{"chapter_num": 3, "topic": "Deeper Into The Darkness"}},
        {{"chapter_num": 4, "topic": "The Shocking Secret"}},
        {{"chapter_num": 5, "topic": "Final Truth Revealed"}}
      ]
    }}
    """
    
    outline_raw = call_gemini(outline_prompt)
    if outline_raw.startswith("```json"): 
        outline_raw = outline_raw[7:-3]
    script_data = json.loads(outline_raw.strip())

    full_story_parts = []
    for ch in script_data['chapters']:
        print(f"📖 Expanding Chapter {ch['chapter_num']}: {ch['topic']}...")
        chapter_prompt = f"""
        Write Chapter {ch['chapter_num']} ({ch['topic']}) for a long storytelling audiobook in Hindi (written in Hinglish Roman Script).
        Requirement: Make it extremely detailed, suspenseful, slow-paced, atmospheric, and descriptive.
        Target length: 800 to 1200 words for this chapter alone.
        Output ONLY the narration story text, no titles or notes.
        """
        narration = call_gemini(chapter_prompt)
        full_story_parts.append(narration)

    script_data['full_narration'] = "\n\n".join(full_story_parts)
    return script_data

async def generate_tts_file(text, filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-2%")
    await communicate.save(filename)

def build_long_video(data, font_path, bg_music_path):
    print("⚡ Building Long Video & Rendering...")

    audio_file = "full_story_audio.mp3"
    print("🗣️ Generating Full Voiceover Audio...")
    asyncio.run(generate_tts_file(data['full_narration'], audio_file))

    voice_clip = AudioFileClip(audio_file)
    total_duration = voice_clip.duration
    print(f"⏱️ Total Video Duration Generated: {round(total_duration / 60, 2)} Minutes!")

    bg_img_path = generate_dark_canvas_image(data['metadata']['title'], "audiobook_cover.png")

    bg_clip = ImageClip(bg_img_path).resize(width=1920, height=1080).set_duration(total_duration)
    bg_clip = bg_clip.resize(lambda t: 1 + 0.002 * t).set_position('center')

    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path)
        if bg_music.duration < total_duration:
            bg_music = bg_music.loop(duration=total_duration)
        else:
            bg_music = bg_music.subclip(0, total_duration)

        bg_music = volumex(bg_music, 0.08)
        from moviepy.audio.AudioClip import CompositeAudioClip
        final_audio = CompositeAudioClip([voice_clip, bg_music])
    else:
        final_audio = voice_clip

    final_video = CompositeVideoClip([bg_clip]).set_audio(final_audio)

    output_filename = "long_audiobook_video.mp4"
    print("🎬 Rendering Final Long MP4 Video...")
    final_video.write_videofile(
        output_filename, 
        fps=15, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast", 
        threads=2, 
        logger=None
    )

    try: 
        os.remove(audio_file)
        os.remove(bg_img_path)
    except: pass

    return output_filename

def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading Long Video to YouTube: {metadata['title']}")
    try:
        token_url = get_url("aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4=")
        creds = Credentials(
            None, 
            refresh_token=os.environ.get("REFRESH_TOKEN"), 
            token_uri=token_url, 
            client_id=os.environ.get("CLIENT_ID"), 
            client_secret=os.environ.get("CLIENT_SECRET")
        )

        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": metadata['title'][:100], 
                "description": metadata['description'], 
                "tags": metadata['tags'], 
                "categoryId": "24"
            },
            "status": {
                "privacyStatus": "public", 
                "selfDeclaredMadeForKids": False
            }
        }
        req = youtube.videos().insert(
            part="snippet,status", 
            body=body, 
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )
        response = req.execute()
        print("🎉 SUCCESS! Long Audiobook Uploaded! Video ID:", response['id'])
    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY Missing!")
        return

    print("🚀 Starting Long Audiobook Automation...")
    font_path = download_font()
    bg_music_path = download_background_music()

    data = generate_long_audiobook_script()
    video_path = build_long_video(data, font_path, bg_music_path)
    upload_to_youtube(video_path, data['metadata'])

    print("✅ Workflow Complete!")

if __name__ == "__main__":
    main()