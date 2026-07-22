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
    # 🎵 Yahan maine trending Emotional, Lofi aur Romantic Piano tracks add kiye hain jo bilkul copyright-free hain!
    music_urls = [
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c3623910.mp3?filename=emotional-piano-107771.mp3", # Deep Emotional Piano
        "https://cdn.pixabay.com/download/audio/2022/10/25/audio_228c2e6f47.mp3?filename=lofi-study-112191.mp3",     # Chill/Sad Lofi
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3?filename=romantic-corporate-10118.mp3", # Warm Romantic
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf756.mp3?filename=romantic-guitars-112134.mp3"  # Acoustic Guitar
    ]
    music_url = random.choice(music_urls)
    
    music_path = "auto_bg_music.mp3"
    if os.path.exists(music_path):
        os.remove(music_path) # Delete old track to get a new one every time
        
    print("🎵 Downloading trending emotional non-copyright music...")
    try:
        res = requests.get(music_url, headers=get_fake_headers(), timeout=20)
        if res.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(res.content)
            print("✅ Emotional Background music downloaded successfully!")
    except Exception as e:
        print(f"⚠️ Could not download background music: {e}")
    return music_path if os.path.exists(music_path) else None

def get_romantic_content_from_gemini():
    print(f"🧠 Requesting Bilingual (Hinglish) Viral Quote via Gemini...")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Instagram style cozy and close-up couple prompts
    themes = [
        "Romantic couple laying on bed looking at each other, cozy mood, highly detailed, cinematic lighting, 8k",
        "Close up of romantic couple holding hands in a cafe, warm aesthetic, emotional vibe, 8k",
        "Aesthetic silhouette of a couple hugging in the rain, dark moody atmosphere, neon lights, 8k",
        "Romantic couple sitting together on a cozy couch, warm fairy lights, intimate mood, 8k"
    ]
    chosen_theme = random.choice(themes)
    
    prompt = f"""
    You are an expert human content creator for a viral Romantic Love Status YouTube channel.
    Current timestamp: {current_time}
    
    Task: Create a completely unique, highly emotional short romantic quote that mixes ENGLISH words with HINDI words (just like Gen-Z/Millennial Instagram Reels).
    Visual Scene: {chosen_theme}
    
    IMPORTANT RULES: 
    1. Mix English and Hindi. Example style: "Limited सी जिंदगी में, Unlimited प्यार है आपसे" or "मेरा Favorite notification सिर्फ तुम हो".
    2. Write the Hindi parts in pure Devanagari script.
    3. Keep the quote VERY short (maximum 2 lines).
    4. DO NOT use emojis inside 'quote_text'. Put emojis only in the title/description.
    
    You must output ONLY a valid JSON object. Do not wrap it in markdown.
    Structure exactly like this:
    {{
      "metadata": {{
        "title": "You are my everything ❤️ #shorts",
        "description": "Tag your favorite person! Subscribe for daily love vibes. 🥰",
        "tags": ["love", "romance", "lofi", "couple", "shorts", "status", "emotional"]
      }},
      "image_prompt": "{chosen_theme}, highly detailed, gorgeous color grading, NO text",
      "quote_text": "मेरी Boring सी life का,\\nसबसे Exciting हिस्सा हो तुम।",
      "text_color": "#FFFFFF",
      "stroke_color": "#000000"
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
    print(f"🎨 Generating Cozy/Romantic Background Image...")
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
    print(f"✍️ Drawing Text (Instagram Reel Style)...")
    w, h = (1080, 1920)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 🛠️ FONT SIZE PERFECT INSTAGRAM SIZE
    font_size = 65
    try: 
        font = ImageFont.truetype(font_path, font_size)
    except: 
        font = ImageFont.load_default()

    wrapped_lines = []
    raw_lines = text.replace('\\n', '\n').split('\n')
    for raw_line in raw_lines:
        wrapped_lines.extend(textwrap.wrap(raw_line, width=22))

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
        
        # 🌟 Instagram Aesthetic Text Effect (Dark thick shadow/outline)
        draw.text((x_text, y_text), line, font=font, fill=text_color, stroke_width=5, stroke_fill="#111111")
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

    print("🎬 Starting Viral 'Hinglish' Emotional Short Generator...")

    font_path = download_hindi_font()
    bg_music_path = download_auto_bg_music()
    
    data = get_romantic_content_from_gemini()
    print(f"📄 Generated Viral Quote: {data['quote_text']}")
    
    bg_image_path = generate_image_free_api(data.get("image_prompt"))
    
    # ⏱️ Viral shorts are usually 7-8 seconds long for high audience retention
    video_duration = 7.0 
    video_w, video_h = (1080, 1920)

    # 1. Background image (Subtle zoom for human feel)
    zoom_factor = random.choice([0.012, 0.015, 0.018])
    bg_clip = ImageClip(bg_image_path).resize(width=video_w, height=video_h)
    bg_clip = bg_clip.resize(lambda t: 1 + zoom_factor * t).set_position('center').set_duration(video_duration)
    
    # Dark vignette/overlay so the white text pops up properly like Instagram
    dark_overlay = ColorClip(size=(video_w, video_h), color=(10,10,10)).set_opacity(0.40).set_duration(video_duration)
    background_final = CompositeVideoClip([bg_clip, dark_overlay])

    # 2. Text overlay
    text_img_file = "static_romantic_text.png"
    text_color = data.get("text_color", "#FFFFFF")
    stroke_color = data.get("stroke_color", "#000000")
    
    create_static_text_image(data['quote_text'], font_path, text_img_file, text_color, stroke_color)
    text_clip = ImageClip(text_img_file).set_duration(video_duration).set_position("center")

    # 3. Emotional Audio setup
    final_audio = None
    if bg_music_path and os.path.exists(bg_music_path):
        try:
            bg_music = AudioFileClip(bg_music_path).subclip(0, video_duration)
            
            # 🎵 Fade In & Fade Out for professional audio feel
            bg_music = bg_music.audio_fadein(1.0).audio_fadeout(1.0)
            bg_music = volumex(bg_music, 0.6) # Volume thoda zyada kiya taaki vibes aayen
            final_audio = bg_music
        except Exception as e:
            print(f"⚠️ Music loading error: {e}")

    final_video = CompositeVideoClip([background_final, text_clip])
    if final_audio:
        final_video.audio = final_audio

    final_video_name = "viral_emotional_reel.mp4"
    
    print("⚡ Rendering Final Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    for f in [text_img_file, "dynamic_bg.jpg"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    upload_video_to_youtube(final_video_name, data['metadata']['title'], data['metadata']['description'], data['metadata']['tags'])
    print("✅ Done! Viral Emotional Video Uploaded Successfully!")

if __name__ == "__main__":
    main()
