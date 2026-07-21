import os
import requests
import json
import urllib.parse
import datetime
import time
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont

# MoviePy for Video Editing & Music
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip
from moviepy.audio.fx.all import volumex

# YouTube API imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading Hindi Font...")
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        with open(font_path, 'wb') as f: 
            f.write(res.content)
    return font_path

def download_auto_bg_music():
    music_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf756.mp3?filename=romantic-guitars-112134.mp3"
    music_path = "auto_bg_music.mp3"
    if not os.path.exists(music_path):
        print("🎵 Downloading copyright-free romantic background music...")
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
    print(f"🧠 Requesting Unique Romantic Quote & Diverse Visual Style via Gemini...")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    themes = [
        "Aesthetic romantic couple silhouette sitting near a window with rain drops, cinematic lighting, 8k",
        "Cozy bedroom with warm fairy lights, romantic couple hugging, cinematic mood, 8k",
        "Beautiful beach sunset silhouette of a romantic couple holding hands, warm golden hour light, 8k",
        "Starry night sky under a glowing full moon with a romantic couple sitting together, magical vibe, 8k",
        "Moody aesthetic coffee shop corner with a romantic couple sharing a moment, cinematic blur, 8k"
    ]
    chosen_theme = random.choice(themes)

    color_palettes = [
        {"text": "#FFFFFF", "stroke": "#000000"}, # White text, Black outline (Classic Aesthetic)
        {"text": "#FFF0F5", "stroke": "#FF1493"}, # Lavender Blush text, Deep Pink outline
        {"text": "#FFD700", "stroke": "#4A0033"}  # Gold text, Deep Purple outline
    ]
    chosen_palette = random.choice(color_palettes)
    
    prompt = f"""
    You are an expert human content creator for a viral Romantic Love Status YouTube channel.
    Current timestamp: {current_time}
    
    Task: Create a completely unique, highly emotional, heart-touching short Hindi romantic quote or shayari in pure Devanagari script.
    Visual Scene Direction to use for image prompt: {chosen_theme}
    
    IMPORTANT RULES: 
    1. Write ONLY in pure Devanagari Hindi script. No emojis inside the quote text.
    2. Keep the quote VERY short (maximum 10-15 words total) so it fits beautifully on screen.
    
    You must output ONLY a valid JSON object. Do not wrap it in markdown.
    Structure exactly like this:
    {{
      "metadata": {{
        "title": "Dil ki baatein ❤️ #shorts",
        "description": "Tag your love. Beautiful romantic feelings and status. Subscribe for daily love quotes.",
        "tags": ["love", "romance", "shayari", "couple", "shorts", "status"]
      }},
      "image_prompt": "{chosen_theme}, highly detailed, gorgeous color grading, NO text, NO watermarks",
      "quote_text": "तेरी आँखों में,\\nमेरा पूरा संसार बसता है।",
      "text_color": "{chosen_palette['text']}",
      "stroke_color": "{chosen_palette['stroke']}"
    }}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 1.2
        }
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if "error" in data:
                if data['error'].get('code') == 503 and attempt < max_retries - 1:
                    print(f"⚠️ Server busy (503). Retrying in {(attempt+1)*5} seconds...")
                    time.sleep((attempt + 1) * 5)
                    continue
                raise Exception(f"API returned an error: {data['error']}")
                
            json_text = data['candidates'][0]['content']['parts'][0]['text']
            
            json_text = json_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            return json.loads(json_text)
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"❌ Gemini Text API Failed after {max_retries} attempts: {e}")
            print(f"⚠️ Attempt {attempt+1} failed. Retrying...")
            time.sleep(5)

def generate_image_free_api(image_prompt):
    print(f"🎨 Generating Unique Romantic Background Image...")
    width, height = (1080, 1920)
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={random.randint(1, 999999)}"
    
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

def create_static_text_image(text, font_path, filename, text_color, stroke_color):
    print(f"✍️ Drawing Text with Auto-Wrapping...")
    w, h = (1080, 1920)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 🛠️ FONT SIZE CHOTA KIYA (Taaki Instagram reel jaisa decent lage)
    font_size = 65
    try: 
        font = ImageFont.truetype(font_path, font_size)
    except: 
        font = ImageFont.load_default()

    # 🛠️ AUTO-WRAPPING LOGIC: Agar line lambi hai toh use center mein break karega
    wrapped_lines = []
    # Agar Gemini ne pehle se \n nahi bheja, toh khud tod denge (max 20 characters per line)
    raw_lines = text.replace('\\n', '\n').split('\n')
    for raw_line in raw_lines:
        wrapped_lines.extend(textwrap.wrap(raw_line, width=22))

    # Calculate total height for perfect vertical centering
    total_height = len(wrapped_lines) * (font_size + 25)
    y_text = (h - total_height) // 2

    for line in wrapped_lines:
        line = line.strip()
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = font.getlength(line)
            
        x_text = (w - line_w) // 2
        
        # Draw dynamic text color and outline
        draw.text((x_text, y_text), line, font=font, fill=text_color, stroke_width=4, stroke_fill=stroke_color)
        y_text += (font_size + 25)

    img.save(filename)
    return filename

def upload_video_to_youtube(video_path, title, description, tags):
    print(f"\n🚀 Uploading to YouTube: {title}")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Video saved locally.")
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

    print("🎬 Starting Human-Like Dynamic Romantic Short Generator...")

    font_path = download_hindi_font()
    bg_music_path = download_auto_bg_music()
    
    data = get_romantic_content_from_gemini()
    print(f"📄 Unique Quote: {data['quote_text']}")
    print(f"🎨 Theme Chosen: {data['image_prompt']}")
    
    bg_image_path = generate_image_free_api(data.get("image_prompt"))
    
    video_duration = 8.0
    video_w, video_h = (1080, 1920)

    # 1. Background image with zoom effect
    zoom_factor = random.choice([0.012, 0.015, 0.018])
    bg_clip = ImageClip(bg_image_path).resize(width=video_w, height=video_h)
    bg_clip = bg_clip.resize(lambda t: 1 + zoom_factor * t).set_position('center').set_duration(video_duration)
    
    dark_overlay = ColorClip(size=(video_w, video_h), color=(10,10,10)).set_opacity(0.45).set_duration(video_duration)
    background_final = CompositeVideoClip([bg_clip, dark_overlay])

    # 2. Text overlay with auto-wrapping
    text_img_file = "static_romantic_text.png"
    text_color = data.get("text_color", "#FFFFFF")
    stroke_color = data.get("stroke_color", "#000000")
    
    create_static_text_image(data['quote_text'], font_path, text_img_file, text_color, stroke_color)
    text_clip = ImageClip(text_img_file).set_duration(video_duration).set_position("center")

    # 3. Audio setup
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
    print("✅ Done! Human-like Dynamic Video Uploaded Successfully!")

if __name__ == "__main__":
    main()
