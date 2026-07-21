import os
import requests
import json
import textwrap
import base64
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import datetime
import asyncio
import edge_tts

# MoviePy for Video Editing
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip

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

def get_everything_from_gemini(video_type):
    print(f"🧠 Requesting {video_type.upper()} Blueprint via Gemini 2.5 Flash REST API...")
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line_count_instruction = "4 lines" if video_type == "short" else "10 to 12 lines"
    
    prompt = f"""
    You are an expert AI Video Director for a Hindu Devotional (Bhakti) YouTube channel.
    Current timestamp to ensure uniqueness: {current_time}
    
    Task: Create a completely unique, NEVER-SEEN-BEFORE {line_count_instruction} highly emotional Hindi Bhakti video script. 
    You randomly choose the deity (e.g., Mahadev, Krishna, Hanuman, Ram). 
    IMPORTANT: Write the Hindi text with commas (,) so the voice pauses naturally.
    
    You must output ONLY a valid JSON object.
    Structure exactly like this:
    {{
      "metadata": {{
        "title": "Catchy Devotional Title Here 🔱",
        "description": "Deep words that touch the soul. Subscribe for daily Bhakti videos.",
        "tags": ["bhakti", "sanatan", "motivation", "status"]
      }},
      "image_prompt": "Ultra realistic, cinematic background of the chosen deity, 8k resolution, highly detailed, beautiful lighting, NO text, NO watermarks",
      "style": {{
        "background_color_fallback": "#1A0000"
      }},
      "lines": [
        {{
          "text": "hindi text with commas for pause",
          "text_color": "#FFFFFF",
          "stroke_color": "#FF0000"
        }}
      ]
    }}
    Rules: Keep Hindi text emotional. DO NOT include extra markdown outside the JSON.
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

def generate_image_free_api(image_prompt, video_type):
    print(f"🎨 Generating Image via Free AI for prompt: '{image_prompt}'...")
    width, height = (1080, 1920) if video_type == "short" else (1920, 1080)
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    img_path = "dynamic_bg.jpg"
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(img_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print("✅ Background Image generated successfully!")
            return img_path
    except Exception as e:
        print(f"⚠️ Failed to generate image: {e}")
    return None

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_dynamic_text_image(text, font_path, filename, text_color, stroke_color, font_size, video_type):
    w, h = (1080, 1920) if video_type == "short" else (1920, 1080)
    wrap_width = 18 if video_type == "short" else 40
    
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype(font_path, font_size)
    except: font = ImageFont.load_default()

    lines = textwrap.wrap(text, width=wrap_width)
    total_height = len(lines) * (font_size + 20)
    y_text = (h - total_height) // 2

    for line in lines:
        try: line_w = font.getlength(line)
        except: line_w = len(line) * (font_size / 2)
        draw.text(((w - line_w) / 2, y_text), line, font=font, fill=text_color, stroke_width=5, stroke_fill=stroke_color)
        y_text += (font_size + 20)

    img.save(filename)
    return filename

# 🔴 YAHAN edge-tts KA USE HUA HAI (Zabardast Viral Voice ke liye)
async def generate_audio_edge(text, filename):
    # 'hi-IN-MadhurNeural' ekdum uss video jaisi deep aur fast storytelling aawaz dega
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+5%", pitch="+0Hz")
    await communicate.save(filename)

def upload_video_to_youtube(video_path, title, description, tags, video_type):
    print(f"\n🚀 Uploading to YouTube: {title}")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Skipping upload.")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)
    
    if video_type == "short" and "#shorts" not in title.lower():
        title += " #shorts"
        if "shorts" not in tags: tags.append("shorts")

    body = {
        "snippet": {"title": title[:100], "description": description[:5000], "tags": tags[:15], "categoryId": "22", "defaultLanguage": "hi"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    try:
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
        response = req.execute()
        url_prefix = "shorts/" if video_type == "short" else "watch?v="
        print(f"🎉 SUCCESS! Video Live at: https://youtube.com/{url_prefix}{response['id']}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY Missing! Exiting...")
        return

    video_type = random.choice(["short", "long"])
    print(f"🎲 AI Decided to make a: {video_type.upper()} VIDEO")

    font_path = download_hindi_font()
    
    data = get_everything_from_gemini(video_type)
    print(f"🎬 Title: {data['metadata']['title']}")
    
    image_prompt = data.get("image_prompt", "Lord Shiva meditating in Himalayas cinematic, no text")
    bg_image_path = generate_image_free_api(image_prompt, video_type)
    
    video_w, video_h = (1080, 1920) if video_type == "short" else (1920, 1080)
    font_size = 80 if video_type == "short" else 70
    
    video_clips = []
    
    for i, line in enumerate(data['lines']):
        print(f"⚙️ Rendering Line {i+1}...")
        
        audio_file = f"line_{i}.mp3"
        
        # 🔴 BADA FIX: Yahan 'asyncio.run' ka use karke edge-tts call kiya hai
        asyncio.run(generate_audio_edge(line['text'], audio_file))
        
        audio_clip = AudioFileClip(audio_file)
        # Ek second ka thehrav jisse video natural lage
        scene_dur = audio_clip.duration + 1.0 
        
        img_file = f"text_{i}.png"
        create_dynamic_text_image(line['text'], font_path, img_file, line['text_color'], line['stroke_color'], font_size, video_type)
        
        animated_text_clip = ImageClip(img_file).set_duration(scene_dur).crossfadein(0.8)
        animated_text_clip = animated_text_clip.set_audio(audio_clip)
        
        video_clips.append(animated_text_clip)

    print("🎞️ Stitching all scenes...")
    final_text_sequence = concatenate_videoclips(video_clips, method="compose")
    
    if bg_image_path and os.path.exists(bg_image_path):
        bg_clip = ImageClip(bg_image_path).resize(width=video_w, height=video_h)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.015 * t).set_position('center').set_duration(final_text_sequence.duration)
        dark_overlay = ColorClip(size=(video_w, video_h), color=(0,0,0)).set_opacity(0.4).set_duration(final_text_sequence.duration)
        bg_clip = CompositeVideoClip([bg_clip, dark_overlay])
    else:
        bg_rgb = hex_to_rgb(data['style'].get("background_color_fallback", "#1A0000"))
        bg_clip = ColorClip(size=(video_w, video_h), color=bg_rgb).set_duration(final_text_sequence.duration)
    
    final_video = CompositeVideoClip([bg_clip, final_text_sequence.set_position("center")])
    final_video.audio = final_text_sequence.audio 
    
    final_video_name = f"automated_bhakti_{video_type}.mp4"
    
    print("⚡ Rendering Final Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    for f in os.listdir("."):
        if f.endswith(".png") or (f.startswith("line_") and f.endswith(".mp3")) or f == "dynamic_bg.jpg":
            try: os.remove(f)
            except: pass

    upload_video_to_youtube(final_video_name, data['metadata']['title'], data['metadata']['description'], data['metadata']['tags'], video_type)
    print("✅ Video Uploaded! Workflow Complete!")

if __name__ == "__main__":
    main()
