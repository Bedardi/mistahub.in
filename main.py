import os
import requests
import asyncio
import json
import textwrap
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# MoviePy for Video Editing
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip, CompositeAudioClip
import moviepy.audio.fx.all as afx

# YouTube API imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Gemini AI
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Using the latest model to avoid 404 errors
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        with open(font_path, 'wb') as f: f.write(res.content)
    return font_path

def get_dynamic_gemini_data():
    print("🧠 Fetching Fully Dynamic Script, Voice, Styles & SEO from Gemini...")
    prompt = """
    Act as a master Video Director and Hindi Shayar. 
    Write a 4-line highly emotional, fresh Hindi Shayari.
    Decide the exact visual style, colors (hex codes), animations, and VOICE parameters for each line to make it stunning.
    You must reply ONLY with a valid JSON format.
    Structure exactly like this:
    {
      "metadata": {
        "title": "Viral Title #shorts",
        "description": "Short description @mistahub",
        "tags": ["tag1", "tag2"]
      },
      "style": {
        "background_color": "#080808",
        "voice_id": "hi-IN-MadhurNeural", 
        "voice_rate": "-5%",
        "voice_pitch": "-2Hz"
      },
      "lines": [
        {
          "text": "hindi text",
          "animation": "typewriter", 
          "text_color": "#FFFFFF",
          "stroke_color": "#FF0000",
          "font_size": 75
        }
      ]
    }
    Rules:
    - Animations allowed: 'typewriter', 'fadein', 'zoom', 'slide_up'.
    - voice_id can be 'hi-IN-MadhurNeural' (Male) or 'hi-IN-SwaraNeural' (Female) based on the emotion.
    - Make sure text_color and stroke_color contrast beautifully with background_color.
    """
    
    try:
        res = model.generate_content(prompt)
        clean_text = res.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"⚠️ Gemini Data Fetch Failed: {e}")
        # Robust Fallback Data
        return {
            "metadata": {"title": "Deep Words 💔 #shorts", "description": "Subscribe @mistahub", "tags": ["shayari", "shorts", "hindi"]},
            "style": {"background_color": "#111111", "voice_id": "hi-IN-MadhurNeural", "voice_rate": "-5%", "voice_pitch": "-2Hz"},
            "lines": [
                {"text": "ज़िंदगी के इस सफर में अजब मोड़ आया", "animation": "typewriter", "text_color": "#FFFFFF", "stroke_color": "#000000", "font_size": 75},
                {"text": "मंजिल का पता नहीं, बस चलता चला गया", "animation": "fadein", "text_color": "#E0E0E0", "stroke_color": "#000000", "font_size": 80},
                {"text": "कुछ खवाब टूटे, कुछ अपने छूटे", "animation": "zoom", "text_color": "#FFFFFF", "stroke_color": "#000000", "font_size": 75},
                {"text": "फिर भी दिल ने कभी हार नहीं माना", "animation": "slide_up", "text_color": "#FFFFFF", "stroke_color": "#000000", "font_size": 80}
            ]
        }

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_dynamic_text_image(text, font_path, filename, text_color, stroke_color, font_size):
    # Ensure background is fully transparent RGBA
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try: font = ImageFont.truetype(font_path, font_size)
    except: font = ImageFont.load_default()

    lines = textwrap.wrap(text, width=20)
    total_height = len(lines) * (font_size + 15)
    y_text = (1920 - total_height) // 2

    for line in lines:
        try: w = font.getlength(line)
        except: w = len(line) * (font_size / 2)
        draw.text(((1080 - w) / 2, y_text), line, font=font, fill=text_color, stroke_width=5, stroke_fill=stroke_color)
        y_text += (font_size + 15)

    img.save(filename)
    return filename

def apply_dynamic_animation(clip, animation_type, duration):
    if animation_type == "typewriter":
        # FIXED: Custom frame logic to avoid lambda/crop errors
        def fl_typewriter(get_frame, t):
            frame = np.copy(get_frame(t))
            # Calculate width to reveal based on time
            w = int((t / duration) * 1080)
            if w < 1080:
                frame[:, w:] = 0  # Make the unrevealed part fully transparent
            return frame
        return clip.fl(lambda gf, t: fl_typewriter(gf, t))
        
    elif animation_type == "zoom":
        return clip.resize(lambda t: 1 + 0.05 * t).set_position('center')
    elif animation_type == "slide_up":
        return clip.set_position(lambda t: ('center', int(100 - (100 * (t/duration)))))
    else: 
        return clip.crossfadein(0.8)

async def generate_audio(text, filename, voice_id, rate, pitch):
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    await communicate.save(filename)

def upload_video_to_youtube(video_path, title, description, tags):
    print("\n🚀 Uploading to YouTube @mistahub...")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing in GitHub Secrets! Skipping upload.")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {"title": title[:100], "description": description[:5000], "tags": tags, "categoryId": "24", "defaultLanguage": "hi"},
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
        print("❌ GEMINI_API_KEY Missing in Secrets! Exiting...")
        return

    font_path = download_hindi_font()
    data = get_dynamic_gemini_data()
    
    print(f"🎬 Executing Directed Video: {data['metadata']['title']}")
    video_clips = []
    
    v_id = data['style'].get('voice_id', 'hi-IN-MadhurNeural')
    v_rate = data['style'].get('voice_rate', '-5%')
    v_pitch = data['style'].get('voice_pitch', '-2Hz')
    
    for i, line in enumerate(data['lines']):
        print(f"⚙️ Processing Line {i+1} with animation: {line.get('animation', 'fadein')}")
        
        audio_file = f"line_{i}.mp3"
        asyncio.run(generate_audio(line['text'], audio_file, v_id, v_rate, v_pitch))
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration + 0.4 
        
        img_file = f"text_{i}.png"
        create_dynamic_text_image(line['text'], font_path, img_file, line['text_color'], line['stroke_color'], line.get('font_size', 75))
        
        animated_clip = apply_dynamic_animation(ImageClip(img_file).set_duration(scene_dur), line['animation'], scene_dur)
        animated_clip = animated_clip.set_audio(audio_clip)
        
        video_clips.append(animated_clip)

    print("🎞️ Stitching all dynamic scenes...")
    final_text_sequence = concatenate_videoclips(video_clips, method="compose")
    
    bg_rgb = hex_to_rgb(data['style'].get("background_color", "#080808"))
    bg_clip = ColorClip(size=(1080, 1920), color=bg_rgb).set_duration(final_text_sequence.duration)
    
    final_video = CompositeVideoClip([bg_clip, final_text_sequence.set_position("center")])
    final_video_name = "ai_shorts_export.mp4"
    
    print("⚡ Rendering Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    for f in os.listdir("."):
        if f.endswith(".png") or (f.startswith("line_") and f.endswith(".mp3")):
            try: os.remove(f)
            except: pass

    upload_video_to_youtube(final_video_name, data['metadata']['title'], data['metadata']['description'], data['metadata']['tags'])
    print("✅ Full Pipeline Execution Complete!")

if __name__ == "__main__":
    main()
