import os
import requests
import json
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import datetime

# MoviePy for Video Editing & Music
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip
from moviepy.audio.fx.all import volumex

# YouTube API imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        with open(font_path, 'wb') as f: f.write(res.content)
    return font_path

def download_auto_bg_music():
    music_path = "auto_bg_music.mp3"
    if not os.path.exists(music_path):
        print("🎵 Downloading copyright-free romantic background music...")
        music_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf756.mp3?filename=romantic-guitars-112134.mp3"
        try:
            res = requests.get(music_url, headers=get_fake_headers(), timeout=20)
            if res.status_code == 200:
                with open(music_path, 'wb') as f:
                    f.write(res.content)
                print("✅ Background music downloaded successfully!")
        except Exception as e:
            print(f"⚠️ Could not download background music: {e}")
    return music_path if os.path.exists(music_path) else None

def get_romantic_content_from_gemini():
    print(f"🧠 Requesting Romantic Quote via Gemini 2.5 Flash...")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
    You are an expert content creator for a viral Romantic Love Status YouTube channel.
    Current timestamp: {current_time}
    
    Task: Create a completely unique, highly emotional, heart-touching 2-line Hindi romantic quote or shayari (like Instagram couple reels).
    
    You must output ONLY a valid JSON object.
    Structure exactly like this:
    {{
      "metadata": {{
        "title": "Limited si zindagi mein unlimited pyaar ❤️ #shorts",
        "description": "Tag your love. Beautiful romantic feelings and status. Subscribe for daily love quotes.",
        "tags": ["love", "romance", "shayari", "couple", "shorts", "status"]
      }},
      "image_prompt": "Cinematic aesthetic romantic couple silhouette in cozy bedroom soft lighting, emotional mood, 8k resolution, highly detailed, NO text, NO watermarks",
      "quote_text": "Limited si zindagi mein,\nUnlimited pyaar hai aapse."
    }}
    Rules: Keep Hindi text deeply emotional. DO NOT include extra markdown outside the JSON.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 1.0
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        if "error" in data:
             raise Exception(f"API returned an error: {data['error']}")
        json_text = data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(json_text)
    except Exception as e:
        raise Exception(f"❌ Gemini Text API Failed: {e}")

def generate_image_free_api(image_prompt):
    print(f"🎨 Generating Romantic Background Image...")
    width, height = (1080, 1920)
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    img_path = "dynamic_bg.jpg"
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(img_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return img_path
    except Exception as e:
        print(f"⚠️ Failed to generate image: {e}")
    return None

def create_static_text_image(text, font_path, filename):
    w, h = (1080, 1920)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_size = 75
    try: font = ImageFont.truetype(font_path, font_size)
    except: font = ImageFont.load_default()

    lines = text.split('\n')
    total_height = len(lines) * (font_size + 25)
    y_text = (h - total_height) // 2

    for line in lines:
        try: line_w = font.getlength(line)
        except: line_w = len(line) * (font_size / 2)
        draw.text(((w - line_w) / 2, y_text), line, font=font, fill="#FFFFFF", stroke_width=6, stroke_fill="#FF1493")
        y_text += (font_size + 25)

    img.save(filename)
    return filename

def upload_video_to_youtube(video_path, title, description, tags):
    print(f"\n🚀 Uploading to YouTube: {title}")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Skipping upload.")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)
    
    if "#shorts" not in title.lower():
        title += " #shorts"
        if "shorts" not in tags: tags.append("shorts")

    body = {
        "snippet": {"title": title[:100], "description": description[:5000], "tags": tags[:15], "categoryId": "22", "defaultLanguage": "hi"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    try:
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
        response = req.execute()
        print(f"🎉 SUCCESS! Video Live at: https://youtube.com/shorts/{response['id']}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY Missing! Exiting...")
        return

    print("🎲 Starting Romantic Short Generator (Static Text + Background Music)...")

    font_path = download_hindi_font()
    bg_music_path = download_auto_bg_music()
    
    data = get_romantic_content_from_gemini()
    print(f"🎬 Title: {data['metadata']['title']}")
    
    bg_image_path = generate_image_free_api(data.get("image_prompt", "Romantic aesthetic couple background"))
    
    video_duration = 8.0
    video_w, video_h = (1080, 1920)

    bg_clip = ImageClip(bg_image_path).resize(width=video_w, height=video_h)
    bg_clip = bg_clip.resize(lambda t: 1 + 0.015 * t).set_position('center').set_duration(video_duration)
    
    dark_overlay = ColorClip(size=(video_w, video_h), color=(15,0,15)).set_opacity(0.45).set_duration(video_duration)
    background_final = CompositeVideoClip([bg_clip, dark_overlay])

    text_img_file = "static_romantic_text.png"
    create_static_text_image(data['quote_text'], font_path, text_img_file)
    text_clip = ImageClip(text_img_file).set_duration(video_duration).set_position("center")

    final_audio = None
    if bg_music_path and os.path.exists(bg_music_path):
        try:
            bg_music = AudioFileClip(bg_music_path).subclip(0, video_duration)
            bg_music = volumex(bg_music, 0.3)
            final_audio = bg_music
        except Exception as e:
            print(f"⚠️ Music loading error: {e}")

    final_video = CompositeVideoClip([background_final, text_clip])
    if final_audio:
        final_video.audio = final_audio

    final_video_name = "romantic_reel_status.mp4"
    
    print("⚡ Rendering Final Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    for f in [text_img_file, "dynamic_bg.jpg"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    upload_video_to_youtube(final_video_name, data['metadata']['title'], data['metadata']['description'], data['metadata']['tags'])
    print("✅ Done! Romantic Video Uploaded Successfully!")

if __name__ == "__main__":
    main()
