import os
import requests
import json
import urllib.parse
import datetime
import time
import random
import textwrap
import asyncio
import base64
import edge_tts
from PIL import Image, ImageDraw, ImageFont

# MoviePy for Video Assembly
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip, concatenate_audioclips
from moviepy.audio.fx.all import volumex

# YouTube API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_url(b64_string):
    return base64.b64decode(b64_string).decode("utf-8")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_font():
    font_path = "BoldFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading Font via REST API...")
        url = get_url("aHR0cHM6Ly9naXRodWIuY29tL2dvb2dsZS9mb250cy9yYXcvbWFpbi9vZmwvbW9udHNlcnJhdC9Nb250c2VycmF0LUJsYWNrLnR0Zg==")
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(font_path, 'wb') as f: 
                f.write(res.content)
    return font_path if os.path.exists(font_path) else None

def download_suspense_music():
    print("🎵 Downloading Background Audio...")
    music_url = get_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8wMy8xNS9hdWRpb181MTE2ZmMwMWMxLm1wMz9maWxlbmFtZT1kYXJrLWFtYmllbnQtMTA3Nzc0Lm1wMw==")
    music_path = "suspense_bg.mp3"
    try:
        res = requests.get(music_url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(res.content)
    except Exception as e:
        print(f"⚠️ Music download skipped: {e}")
    return music_path if os.path.exists(music_path) else None

def get_psychology_script():
    print("🧠 Generating Script via Gemini REST API...")
    
    prompt = """
    Act as a viral YouTube Shorts scriptwriter in the 'Dark Psychology & Human Behavior' niche.
    Target audience: India (Use Hinglish - A mix of Hindi in Roman English script and English words).
    
    Write a highly engaging, mysterious 3-part script. 
    Rule 1: The 'hook' must be shocking and under 3 seconds.
    Rule 2: The 'body' must reveal a fascinating psychological trick or human behavior fact.
    Rule 3: The 'outro' must ask them to subscribe or comment.
    
    Output ONLY valid JSON. Structure exactly like this:
    {
      "metadata": {
        "title": "This psychological trick is scary 🤯 #shorts #psychology",
        "description": "Learn human behavior secrets. Subscribe for more! #darkpsychology",
        "tags": ["psychology", "darkpsychology", "bodylanguage", "shorts", "facts"]
      },
      "image_prompt": "Dark mysterious silhouette of a person standing in foggy cinematic street, neon lights, 8k highly detailed",
      "hook_text": "Kya aapko pata hai ki log aapse jhooth kaise bolte hain?",
      "body_text": "Psychology kehti hai ki jab koi jhooth bolta hai, toh wo apni naak ya chehre ko baar-baar touch karta hai.",
      "outro_text": "Apne dosto ko bhej kar unka jhooth pakdo, aur subscribe karo!"
    }
    """

    base_url = get_url("aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL21vZGVscy9nZW1pbmktMi41LWZsYXNoOmdlbmVyYXRlQ29udGVudD9rZXk9")
    url = base_url + str(GEMINI_API_KEY)
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
    
    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
    data = res.json()
    
    json_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
    if json_text.startswith("```json"): 
        json_text = json_text[7:-3]
    return json.loads(json_text.strip())

def generate_image(prompt):
    print("🎨 Generating Cinematic Background via REST API...")
    img_path = "bg_image.jpg"
    
    safe_prompt = prompt + ", dark aesthetic, mystery, 4k resolution, no text"
    encoded_prompt = urllib.parse.quote(safe_prompt)
    
    base_url = get_url("aHR0cHM6Ly9pbWFnZS5wb2xsaW5hdGlvbnMuYWkvcHJvbXB0Lw==")
    url = base_url + encoded_prompt + "?width=1080&height=1920&nologo=true"
    
    try:
        res = requests.get(url, stream=True, timeout=30)
        if res.status_code == 200:
            with open(img_path, 'wb') as f:
                for chunk in res.iter_content(1024): 
                    f.write(chunk)
            print("✅ Background Image Downloaded Successfully!")
            return img_path
    except Exception as e:
        print(f"⚠️ Image API error: {e}")
        
    img = Image.new('RGB', (1080, 1920), color=(15, 15, 20))
    img.save(img_path)
    return img_path

async def generate_ai_voice(text, filename):
    communicate = edge_tts.Communicate(text, "en-IN-PrabhatNeural", rate="+5%") 
    await communicate.save(filename)

def create_text_image(text, font_path, filename):
    w, h = 1080, 1920
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_size = 65
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        
    wrapped_lines = []
    raw_lines = text.replace('\\n', '\n').split('\n')
    for raw_line in raw_lines:
        wrapped_lines.extend(textwrap.wrap(raw_line, width=22))
        
    total_height = len(wrapped_lines) * (font_size + 20)
    y_text = (h - total_height) // 2
    
    for line in wrapped_lines:
        line = line.strip()
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = font.getlength(line)
            
        x_text = (w - line_w) // 2
        draw.text((x_text, y_text), line, font=font, fill="white", stroke_width=4, stroke_fill="black")
        y_text += (font_size + 20)
        
    img.save(filename)
    return filename

def build_video(data, font_path, bg_music_path, bg_img_path):
    print("⚡ Assembling Video...")
    
    asyncio.run(generate_ai_voice(data['hook_text'], "audio_hook.mp3"))
    asyncio.run(generate_ai_voice(data['body_text'], "audio_body.mp3"))
    asyncio.run(generate_ai_voice(data['outro_text'], "audio_outro.mp3"))

    audio_hook = AudioFileClip("audio_hook.mp3")
    audio_body = AudioFileClip("audio_body.mp3")
    audio_outro = AudioFileClip("audio_outro.mp3")
    
    t1, t2, t3 = audio_hook.duration, audio_body.duration, audio_outro.duration
    total_duration = t1 + t2 + t3
    final_voice = concatenate_audioclips([audio_hook, audio_body, audio_outro])
    
    bg_clip = ImageClip(bg_img_path).resize(width=1080, height=1920)
    bg_clip = bg_clip.resize(lambda t: 1 + 0.015 * t).set_position('center').set_duration(total_duration)
    dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.6).set_duration(total_duration)
    
    create_text_image(data['hook_text'], font_path, "text_hook.png")
    create_text_image(data['body_text'], font_path, "text_body.png")
    create_text_image(data['outro_text'], font_path, "text_outro.png")
    
    clip_hook = ImageClip("text_hook.png").set_start(0).set_duration(t1).set_position('center')
    clip_body = ImageClip("text_body.png").set_start(t1).set_duration(t2).set_position('center')
    clip_outro = ImageClip("text_outro.png").set_start(t1 + t2).set_duration(t3).set_position('center')
    
    final_video = CompositeVideoClip([bg_clip, dark_overlay, clip_hook, clip_body, clip_outro])
    
    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path).subclip(0, total_duration)
        bg_music = volumex(bg_music, 0.15)
        from moviepy.audio.AudioClip import CompositeAudioClip
        final_video.audio = CompositeAudioClip([final_voice, bg_music])
    else:
        final_video.audio = final_voice
    
    output_filename = "viral_psychology_short.mp4"
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)
    
    for f in ["audio_hook.mp3", "audio_body.mp3", "audio_outro.mp3", "text_hook.png", "text_body.png", "text_outro.png", bg_img_path]:
        try: os.remove(f)
        except: pass
        
    return output_filename

def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    try:
        token_url = get_url("aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4=")
        
        creds = Credentials(None, refresh_token=os.environ.get("REFRESH_TOKEN"), 
                            token_uri=token_url, 
                            client_id=os.environ.get("CLIENT_ID"), 
                            client_secret=os.environ.get("CLIENT_SECRET"))
        
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {"title": metadata['title'][:100], "description": metadata['description'], "tags": metadata['tags'], "categoryId": "22"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        }
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, resumable=True))
        response = req.execute()
        print("🎉 SUCCESS! Video Live ID:", response['id'])
    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing!")
        return
        
    print("🎬 Starting Dark Psychology Automation...")
    font_path = download_font()
    bg_music_path = download_suspense_music()
    
    data = get_psychology_script()
    bg_image_path = generate_image(data['image_prompt'])
    
    video_path = build_video(data, font_path, bg_music_path, bg_image_path)
    upload_to_youtube(video_path, data['metadata'])
    
    print("✅ Workflow Complete!")

if __name__ == "__main__":
    main()
