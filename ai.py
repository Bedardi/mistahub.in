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
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, 
    concatenate_videoclips, concatenate_audioclips
)
from moviepy.audio.fx.all import volumex

# YouTube API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# GEMINI API Key from environment
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
    print("🎵 Downloading Background Ambient Music...")
    music_url = get_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8wMy8xNS9hdWRpb181MTE2ZmMwMWMxLm1wMz9maWxlbmFtZT1kYXJrLWFtYmllbnQtMTA3Nzc0Lm1wMw==")
    music_path = "ambient_bg.mp3"
    try:
        res = requests.get(music_url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(res.content)
    except Exception as e:
        print(f"⚠️ Music download skipped: {e}")
    return music_path if os.path.exists(music_path) else None

def get_fresh_audiobook_script():
    print("🧠 Generating Fresh Long-form Audiobook Script via Gemini API...")

    genres = ["Horror Mystery", "Dark Psychology Secrets", "Historical Untold Mystery", "Mind Blowing Sci-Fi Thriller", "Ancient Mythology Secrets"]
    selected_genre = random.choice(genres)
    
    prompt = f"""
    You are a professional YouTube Audiobook scriptwriter in the '{selected_genre}' genre.
    Target Audience: Indian Viewers (Write in conversational Hinglish - Hindi written in Hinglish script with simple vocabulary).
    
    Create a fresh, captivating, dark/mysterious story divided into 5 to 6 distinct sequential scenes.
    
    Output strictly in VALID JSON format like this:
    {{
      "metadata": {{
        "title": "Uncaught Title - Complete Story Hindi Audiobook",
        "description": "Listen to this thrilling story till the end... #audiobook #hindi #mystic #story",
        "tags": ["audiobook", "hindi story", "thriller", "mystery", "psychology"]
      }},
      "scenes": [
        {{
          "scene_num": 1,
          "narration_text": "Saal 1995 ki baat hai, ek chote se gaaon me ek aisi ghatna ghati jisne sabko hairan kar diya...",
          "image_prompt": "Cinematic 16:9 view of an abandoned mysterious foggy village in night, cinematic lighting, 8k dark fantasy"
        }},
        {{
          "scene_num": 2,
          "narration_text": "Gaaon ke purane mandir ke paas har raat ek ajeeb sa saaya dekha jata tha...",
          "image_prompt": "Cinematic shot of an ancient ruined Indian temple illuminated by moonlight, mysterious fog, eerie aesthetic"
        }}
      ]
    }}
    """

    # Using Gemini 1.5 Flash Endpoint
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key="
    url = base_url + str(GEMINI_API_KEY)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.85}
    }

    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=40)
    data = res.json()

    try:
        json_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        if json_text.startswith("```json"): 
            json_text = json_text[7:-3]
        return json.loads(json_text.strip())
    except Exception as e:
        print("❌ Error parsing Gemini JSON output:", e)
        print("Response received:", data)
        raise e

def generate_scene_image(prompt, scene_num):
    print(f"🎨 Generating Scene {scene_num} Image...")
    img_path = f"bg_scene_{scene_num}.jpg"

    safe_prompt = prompt + ", 16:9 widescreen, cinematic lighting, photorealistic, 4k resolution, highly detailed, no text"
    encoded_prompt = urllib.parse.quote(safe_prompt)

    # Pollinations AI 16:9 (1920x1080)
    base_url = "https://image.pollinations.ai/prompt/"
    url = f"{base_url}{encoded_prompt}?width=1920&height=1080&nologo=true&seed={random.randint(100, 99999)}"

    try:
        res = requests.get(url, stream=True, timeout=30)
        if res.status_code == 200:
            with open(img_path, 'wb') as f:
                for chunk in res.iter_content(1024): 
                    f.write(chunk)
            return img_path
    except Exception as e:
        print(f"⚠️ Image API error for scene {scene_num}: {e}")

    # Fallback blank dark background
    img = Image.new('RGB', (1920, 1080), color=(15, 15, 20))
    img.save(img_path)
    return img_path

async def generate_ai_voice(text, filename):
    # Hindi/Hinglish Audiobook Voice (Madhur or Swara)
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-2%") 
    await communicate.save(filename)

def create_subtitled_scene_image(bg_img_path, text, font_path, scene_num):
    # Overlay subtitles on widescreen 1920x1080 image
    img = Image.open(bg_img_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    w, h = 1920, 1080

    font_size = 45
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # Text wrapping for 1920 width
    wrapped_lines = textwrap.wrap(text, width=55)

    line_height = font_size + 15
    total_text_height = len(wrapped_lines) * line_height
    y_start = h - total_text_height - 80 # Place near bottom

    # Draw semi-transparent dark box behind subtitle for readability
    padding = 20
    draw.rectangle([100, y_start - padding, w - 100, y_start + total_text_height + padding], fill=(0, 0, 0, 160))

    y_text = y_start
    for line in wrapped_lines:
        line = line.strip()
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = font.getlength(line)

        x_text = (w - line_w) // 2
        draw.text((x_text, y_text), line, font=font, fill="yellow", stroke_width=2, stroke_fill="black")
        y_text += line_height

    out_path = f"final_frame_{scene_num}.png"
    img.convert('RGB').save(out_path)
    return out_path

def build_audiobook_video(data, font_path, bg_music_path):
    print("⚡ Assembling Long Audiobook Video...")
    
    scene_clips = []
    audio_clips = []
    temp_files = []

    for idx, scene in enumerate(data['scenes']):
        scene_num = idx + 1
        text = scene['narration_text']
        img_prompt = scene['image_prompt']

        # 1. Voiceover for scene
        audio_file = f"audio_scene_{scene_num}.mp3"
        asyncio.run(generate_ai_voice(text, audio_file))
        audio_clip = AudioFileClip(audio_file)
        audio_clips.append(audio_clip)
        temp_files.append(audio_file)

        # 2. Image generation & Subtitle Overlay
        raw_img = generate_scene_image(img_prompt, scene_num)
        subtitled_img = create_subtitled_scene_image(raw_img, text, font_path, scene_num)
        temp_files.extend([raw_img, subtitled_img])

        # 3. Create Scene Video Clip with slight Zoom / Ken-Burns effect
        img_clip = ImageClip(subtitled_img).resize(width=1920, height=1080)
        img_clip = img_clip.set_duration(audio_clip.duration).set_audio(audio_clip)
        
        # Smooth zoom effect
        img_clip = img_clip.resize(lambda t: 1 + 0.008 * t).set_position('center')
        
        scene_clips.append(img_clip)

    # Combine scenes sequentially
    final_video = concatenate_videoclips(scene_clips, method="compose")
    total_duration = final_video.duration

    # Add Ambient Background Music
    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path)
        # Loop music if video is longer
        if bg_music.duration < total_duration:
            bg_music = bg_music.loop(duration=total_duration)
        else:
            bg_music = bg_music.subclip(0, total_duration)
        
        bg_music = volumex(bg_music, 0.10) # 10% volume so voiceover is clear
        
        from moviepy.audio.AudioClip import CompositeAudioClip
        final_video.audio = CompositeAudioClip([final_video.audio, bg_music])

    output_filename = "final_audiobook_video.mp4"
    print(f"🎬 Rendering Video (Total Duration: {round(total_duration, 1)} seconds)...")
    final_video.write_videofile(
        output_filename, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        preset="medium", 
        threads=2, 
        logger=None
    )

    # Cleanup temporary files
    for f in temp_files:
        try: os.remove(f)
        except: pass

    return output_filename

def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
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
                "categoryId": "24" # Entertainment / Story
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
        print("🎉 SUCCESS! YouTube Video Live ID:", response['id'])
    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY environment variable missing!")
        return

    print("🎬 Starting Hindi Audiobook Automation Pipeline...")
    font_path = download_font()
    bg_music_path = download_background_music()

    # Step 1: Dynamic Scripting via Gemini
    script_data = get_fresh_audiobook_script()

    # Step 2: Assemble Video with Scenes, Audio, Subtitles
    video_file = build_audiobook_video(script_data, font_path, bg_music_path)

    # Step 3: Auto Upload to YouTube
    upload_to_youtube(video_file, script_data['metadata'])

    print("✅ Audiobook Workflow Complete!")

if __name__ == "__main__":
    main()