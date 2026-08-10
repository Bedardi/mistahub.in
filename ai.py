import os
import requests
import json
import time
import random
import textwrap
import asyncio
import base64
import edge_tts
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

# MoviePy
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.audio.fx.all import volumex
from moviepy.audio.AudioClip import CompositeAudioClip

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
    print("🎵 Downloading Ambient Audio...")
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

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.85}
    }
    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    data = res.json()
    if res.status_code == 200 and 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text'].strip()
    return ""

def generate_dark_canvas_image(title_text, filename="background.png"):
    print("🎨 Creating Dark Canvas...")
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
        draw.text((x, y), line, font=font, fill=(240, 240, 240))
        y += 75

    img.save(filename)
    return filename

def generate_chapter(ch):
    print(f"📖 Expanding Chapter {ch['chapter_num']}...")
    chapter_prompt = f"Write Chapter {ch['chapter_num']} ({ch['topic']}) for a long storytelling audiobook in Hindi (Hinglish Roman Script). Requirement: suspenseful, atmospheric. Length: 800-1000 words. Output ONLY narration."
    return call_gemini(chapter_prompt)

def generate_long_audiobook_script():
    print("🧠 Outlining Story via Gemini API...")
    genres = ["Mystery Horror", "Psychological Thriller"]
    outline_prompt = f"""You are a YouTube Creator. Create an outline for a long Hinglish story in '{random.choice(genres)}'. Divide into 5 Chapters. Output JSON ONLY:
    {{"metadata": {{"title": "Title here", "description": "Desc here", "tags": ["tag1"]}}, "chapters": [{{"chapter_num": 1, "topic": "Topic"}}]}}"""
    
    outline_raw = call_gemini(outline_prompt)
    if outline_raw.startswith("```json"): outline_raw = outline_raw[7:-3]
    script_data = json.loads(outline_raw.strip())

    # 🔥 PARALLEL API CALLS (Bahut time bachega isse)
    with ThreadPoolExecutor(max_workers=5) as executor:
        chapters_text = list(executor.map(generate_chapter, script_data['chapters']))

    script_data['full_narration'] = "\n\n".join(chapters_text)
    return script_data

async def generate_tts_file(text, filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+5%") # Increased speed slightly
    await communicate.save(filename)

def build_long_video(data, bg_img_path, bg_music_path):
    print("⚡ Building Video...")
    audio_file = "full_story_audio.mp3"
    asyncio.run(generate_tts_file(data['full_narration'], audio_file))

    voice_clip = AudioFileClip(audio_file)
    total_duration = voice_clip.duration
    print(f"⏱️ Duration: {round(total_duration / 60, 2)} Mins")

    # 🔥 ZOOM EFFECT REMOVED! Only Static image (Lightning Fast Render)
    bg_clip = ImageClip(bg_img_path).resize(width=1920, height=1080).set_duration(total_duration)

    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path)
        bg_music = bg_music.loop(duration=total_duration) if bg_music.duration < total_duration else bg_music.subclip(0, total_duration)
        bg_music = volumex(bg_music, 0.08)
        final_audio = CompositeAudioClip([voice_clip, bg_music])
    else:
        final_audio = voice_clip

    final_video = CompositeVideoClip([bg_clip]).set_audio(final_audio)

    output_filename = "long_audiobook_video.mp4"
    print("🎬 Rendering Final MP4 Video... (This will be much faster now)")
    
    # 🔥 FPS REDUCED TO 1 (Since it's a static image)
    final_video.write_videofile(
        output_filename, 
        fps=1, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast", 
        threads=4, 
        logger=None
    )
    return output_filename

def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    # YouTube upload logic remains same
    pass

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY Missing!")
        return

    print("🚀 Starting Fast Automation...")
    bg_music_path = download_background_music()
    data = generate_long_audiobook_script()
    bg_img_path = generate_dark_canvas_image(data['metadata']['title'], "cover.png")
    
    video_path = build_long_video(data, bg_img_path, bg_music_path)
    # upload_to_youtube(video_path, data['metadata']) 
    print("✅ Workflow Complete!")

if __name__ == "__main__":
    main()
