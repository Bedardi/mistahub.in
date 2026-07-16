import os
import requests
import asyncio
import json
import textwrap
import edge_tts
import base64
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import datetime

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

def get_everything_from_gemini():
    print("🧠 Requesting Video Blueprint via Gemini 2.5 Flash...")
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
    You are an expert AI Video Director for a Hindu Devotional (Bhakti) YouTube channel.
    Current timestamp to ensure uniqueness: {current_time}
    
    Task: Create a completely unique, NEVER-SEEN-BEFORE 4-line highly emotional Hindi Bhakti video script. 
    You randomly choose the deity (e.g., Mahadev, Krishna, Hanuman, Ram, Durga) and the life lesson (e.g., karma, strength, patience, letting go). 
    Do NOT use the same concepts twice.
    
    You must output ONLY a valid JSON object.
    Structure exactly like this:
    {{
      "metadata": {{
        "title": "Catchy Devotional Title Here 🔱 #shorts",
        "description": "Deep words that touch the soul. Subscribe for daily Bhakti videos.",
        "tags": ["bhakti", "shorts", "sanatan", "motivation", "status"]
      }},
      "image_prompt": "A highly detailed, cinematic AI image prompt for the background. Specify that the image MUST NOT have any text or letters in it. Example: 'Cinematic wide shot of Lord Mahadev meditating on Mount Kailash in heavy snow, highly detailed face, realistic, 8k resolution, no text, no watermarks'",
      "style": {{
        "voice_gender": "Male",
        "voice_rate": "-5%",
        "voice_pitch": "-3Hz",
        "background_color_fallback": "#1A0000"
      }},
      "lines": [
        {{
          "text": "hindi text line 1",
          "animation": "zoom", 
          "text_color": "#FFFFFF",
          "stroke_color": "#FF0000",
          "font_size": 75
        }}
      ]
    }}
    Rules:
    - Keep Hindi text emotional and impactful.
    - Animations allowed: 'typewriter', 'fadein', 'zoom', 'slide_up'.
    """
    
    # ✅ Updated to models/gemini-2.5-flash
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
        blueprint = json.loads(json_text)
        print("✅ Received JSON Blueprint successfully!")
        return blueprint
    except Exception as e:
        raise Exception(f"❌ Gemini Text API Failed: {e}\nAPI Response: {response.text}")

def generate_image_with_gemini(image_prompt):
    print(f"🎨 Generating Image via Imagen 4.0 for prompt: '{image_prompt}'...")
    
    # ✅ Updated to models/imagen-4.0-generate-001
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": image_prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "9:16",
            "outputOptions": {"mimeType": "image/jpeg"}
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if "predictions" in data and len(data["predictions"]) > 0:
            image_data = data["predictions"][0]["bytesBase64Encoded"]
            img_path = "dynamic_bg.jpg"
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            print("✅ Background Image generated!")
            return img_path
        else:
            print(f"⚠️ Image Response Error: {data}")
            return None
    except Exception as e:
        print(f"⚠️ Image Request Failed: {e}")
        return None

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_dynamic_text_image(text, font_path, filename, text_color, stroke_color, font_size):
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype(font_path, font_size)
    except: font = ImageFont.load_default()

    lines = textwrap.wrap(text, width=18)
    total_height = len(lines) * (font_size + 20)
    y_text = (1920 - total_height) // 2

    for line in lines:
        try: w = font.getlength(line)
        except: w = len(line) * (font_size / 2)
        draw.text(((1080 - w) / 2, y_text), line, font=font, fill=text_color, stroke_width=5, stroke_fill=stroke_color)
        y_text += (font_size + 20)

    img.save(filename)
    return filename

def apply_dynamic_animation(clip, animation_type, duration):
    if animation_type == "typewriter":
        def fl_typewriter(get_frame, t):
            frame = np.copy(get_frame(t))
            w = int((t / duration) * 1080)
            if w < 1080: frame[:, w:] = 0
            return frame
        return clip.fl(lambda gf, t: fl_typewriter(gf, t))
    elif animation_type == "zoom":
        return clip.resize(lambda t: 1 + 0.05 * t).set_position('center')
    elif animation_type == "slide_up":
        return clip.set_position(lambda t: ('center', int(100 - (100 * (t/duration)))))
    else: 
        return clip.crossfadein(0.8)

async def generate_audio(text, filename, voice_gender, rate, pitch):
    voice_id = "hi-IN-MadhurNeural" if voice_gender.lower() == "male" else "hi-IN-SwaraNeural"
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    await communicate.save(filename)

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

    font_path = download_hindi_font()
    
    data = get_everything_from_gemini()
    print(f"🎬 Title: {data['metadata']['title']}")
    
    image_prompt = data.get("image_prompt", "Lord Shiva meditating in Himalayas cinematic, no text")
    bg_image_path = generate_image_with_gemini(image_prompt)
    
    video_clips = []
    v_gender = data['style'].get('voice_gender', 'Male')
    v_rate = data['style'].get('voice_rate', '-5%')
    v_pitch = data['style'].get('voice_pitch', '-2Hz')
    
    for i, line in enumerate(data['lines']):
        print(f"⚙️ Rendering Line {i+1}...")
        
        audio_file = f"line_{i}.mp3"
        asyncio.run(generate_audio(line['text'], audio_file, v_gender, v_rate, v_pitch))
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration + 0.6 
        
        img_file = f"text_{i}.png"
        create_dynamic_text_image(line['text'], font_path, img_file, line['text_color'], line['stroke_color'], line.get('font_size', 80))
        
        animated_text_clip = apply_dynamic_animation(ImageClip(img_file).set_duration(scene_dur), line.get('animation', 'fadein'), scene_dur)
        animated_text_clip = animated_text_clip.set_audio(audio_clip)
        
        video_clips.append(animated_text_clip)

    final_text_sequence = concatenate_videoclips(video_clips, method="compose")
    
    if bg_image_path and os.path.exists(bg_image_path):
        bg_clip = ImageClip(bg_image_path).resize(width=1080, height=1920)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.015 * t).set_position('center').set_duration(final_text_sequence.duration)
        dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.4).set_duration(final_text_sequence.duration)
        bg_clip = CompositeVideoClip([bg_clip, dark_overlay])
    else:
        bg_rgb = hex_to_rgb(data['style'].get("background_color_fallback", "#1A0000"))
        bg_clip = ColorClip(size=(1080, 1920), color=bg_rgb).set_duration(final_text_sequence.duration)
    
    final_video = CompositeVideoClip([bg_clip, final_text_sequence.set_position("center")])
    final_video_name = "fully_automated_bhakti_shorts.mp4"
    
    print("⚡ Rendering Final Animated Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    for f in os.listdir("."):
        if f.endswith(".png") or (f.startswith("line_") and f.endswith(".mp3")) or f == "dynamic_bg.jpg":
            try: os.remove(f)
            except: pass

    upload_video_to_youtube(final_video_name, data['metadata']['title'], data['metadata']['description'], data['metadata']['tags'])
    print("✅ Video Uploaded! Workflow Complete!")

if __name__ == "__main__":
    main()
