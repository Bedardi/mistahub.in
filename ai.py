import os
import sys
import subprocess
import base64
import textwrap

# ==========================================
# 1. AUTO-INSTALLER
# ==========================================
def install_packages():
    print("⚙️ Checking dependencies...")
    try:
        import requests
        import edge_tts
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("📦 Installing required packages automatically...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "edge-tts", "pillow"])
        print("✅ Packages installed successfully!\n")

install_packages()

import requests
import json
import random
import urllib.parse
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# 2. HELPER FUNCTIONS & DECODERS
# ==========================================
def get_safe_url(b64_string):
    return base64.b64decode(b64_string).decode("utf-8")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_font():
    font_path = "BoldFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading Font for Captions...")
        # Using a clean sans-serif font suitable for shorts
        url = get_safe_url("aHR0cHM6Ly9naXRodWIuY29tL2dvb2dsZS9mb250cy9yYXcvbWFpbi9vZmwvcm9ib3RvL1JvYm90by1CbGFjay50dGY=")
        try:
            res = requests.get(url, headers=get_fake_headers(), timeout=15)
            if res.status_code == 200:
                with open(font_path, 'wb') as f: f.write(res.content)
        except Exception as e:
            print(f"⚠️ Font download failed: {e}")
    return font_path if os.path.exists(font_path) else None

def download_sad_bgm():
    print("🎵 Downloading Sad/Emotional BGM...")
    # Using a sad cinematic piano loop
    url = get_safe_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8xMC8yNS9hdWRpb18yM2I0NjIyZjVlLm1wMz9maWxlbmFtZT1zYWQtY2luZW1hdGljLXBpYW5vLTEyMzk3MC5tcDM=")
    music_path = "sad_bg.mp3"
    try:
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f: f.write(res.content)
    except: pass
    return music_path if os.path.exists(music_path) else None

def call_gemini(prompt):
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
    base_api = get_safe_url("aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL21vZGVscy8=")

    for model in models:
        url = f"{base_api}{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.9}} # High temp for creativity
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            data = res.json()
            if res.status_code == 200 and 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except: pass
    return ""

def generate_pollinations_image_vertical(prompt, filename):
    print(f"🎨 Generating AI Background: {filename}...")
    # CHANGED TO VERTICAL (1080x1920) FOR SHORTS
    safe_prompt = urllib.parse.quote("Cinematic, moody, aesthetic, 4k, " + prompt)
    base_img = get_safe_url("aHR0cHM6Ly9pbWFnZS5wb2xsaW5hdGlvbnMuYWkvcHJvbXB0Lw==")
    url = f"{base_img}{safe_prompt}?width=1080&height=1920&nologo=true"

    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(filename, 'wb') as f: f.write(res.content)
            return filename
    except: pass
    img = Image.new('RGB', (1080, 1920), color=(15, 20, 25))
    img.save(filename)
    return filename

# ==========================================
# CUSTOM LIP-SYNC CAPTIONS GENERATOR 
# ==========================================
async def generate_tts_with_subs(text, audio_filename, vtt_filename):
    # -10% rate for slower, emotional delivery
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-10%", pitch="-5Hz")
    subs = []

    with open(audio_filename, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                offset_sec = chunk["offset"] / 10_000_000.0
                duration_sec = chunk["duration"] / 10_000_000.0

                def format_vtt(sec):
                    h = int(sec // 3600)
                    m = int((sec % 3600) // 60)
                    s = int(sec % 60)
                    ms = int(round((sec - int(sec)) * 1000))
                    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

                start_time = format_vtt(offset_sec)
                end_time = format_vtt(offset_sec + duration_sec)
                word = chunk["text"]

                subs.append(f"{start_time} --> {end_time}\n{word}\n")

    with open(vtt_filename, "w", encoding="utf-8") as file:
        file.write("WEBVTT\n\n")
        file.write("\n".join(subs))


# ==========================================
# 3. GEMINI SHAYARI GENERATOR
# ==========================================
def get_shayari_from_gemini():
    print("🔍 Asking Gemini AI for Emotional Shayari...")
    
    prompt = """
    You are an expert at writing heart-touching, deep, emotional Shayari in Hindi (written in Hinglish script).
    Create 1 Short Video Script (Max 20 seconds of speaking).
    
    Themes to choose randomly from: Loneliness, Fake friends, Lost Love, Deep life truth, Broken heart.
    
    CRITICAL RULE: DO NOT USE EMOJIS in the JSON output. Keep text clean.
    
    Generate JSON exactly in this format:
    {
      "metadata": {
        "title": "[Catchy Title] 💔 #shorts #shayari", 
        "description": "Deep words about life... #emotional #quotes #hindishayari", 
        "tags": ["shorts", "shayari", "emotional", "deep quotes", "hindi", "sad status"]
      },
      "slides": [
        {
          "visual_prompt": "A lonely person walking on a dark rainy street, moody lighting",
          "narration": "Log kehte hain waqt ke sath sab theek ho jata hai..."
        },
        {
          "visual_prompt": "A broken glass, dark aesthetic background",
          "narration": "Par sach toh ye hai, dard wahi rehta hai, bas hume sehna aa jata hai."
        }
      ]
    }
    """
    response = call_gemini(prompt)
    if response.startswith("```json"): response = response[7:-3]
    try: return json.loads(response.strip())
    except: return None

# ==========================================
# 5. FFMPEG VIDEO ASSEMBLY (SHORTS FORMAT)
# ==========================================
def build_chapter_video(image_path, audio_path, vtt_path, output_path):
    print(f"⚡ Rendering {output_path} (Vertical Shorts)...")
    
    # Changed MarginV to bring subtitles lower to the middle of the vertical screen
    # Added commas in text if needed for pauses, FFmpeg handles VTT words
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles={vtt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Shadow=2,Alignment=2,MarginV=150'",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def assemble_final_video(parts_data, bg_music=None):
    print("🎬 Starting FFmpeg Assembly for SHORTS...")
    video_files = []

    for idx, part in enumerate(parts_data):
        audio_file = f"temp_audio_{idx}.mp3"
        vtt_file = f"temp_sub_{idx}.vtt"
        vid_file = f"temp_part_{idx}.mp4"

        # Generate Audio and Custom VTT
        asyncio.run(generate_tts_with_subs(part['text'], audio_file, vtt_file))
        
        # Generate Vertical Image based on Gemini's prompt
        img_file = generate_pollinations_image_vertical(part['slide_data']['visual_prompt'], f"temp_img_{idx}.jpg")

        build_chapter_video(img_file, audio_file, vtt_file, vid_file)
        video_files.append(vid_file)

    print("🔗 Concatenating All Parts...")
    with open("concat.txt", "w") as f:
        for vid in video_files: f.write(f"file '{vid}'\n")

    merged_vid = "merged_no_bgm.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", merged_vid], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    final_output = "final_ready_short.mp4"
    if bg_music and os.path.exists(bg_music):
        print("🎧 Adding Sad Background Music...")
        # Volume set to 0.15 for BGM so voice is clearly heard
        cmd = [
            "ffmpeg", "-y", "-i", merged_vid, "-stream_loop", "-1", "-i", bg_music,
            "-filter_complex", "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", final_output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        os.rename(merged_vid, final_output)

    print("🧹 Cleaning up temp files...")
    try:
        os.remove("concat.txt")
        for i in range(len(parts_data)):
            os.remove(f"temp_audio_{i}.mp3")
            os.remove(f"temp_sub_{i}.vtt")
            os.remove(f"temp_part_{i}.mp4")
            os.remove(f"temp_img_{i}.jpg")
        if os.path.exists("merged_no_bgm.mp4"): os.remove("merged_no_bgm.mp4")
    except: pass

    return final_output

# ==========================================
# 6. YOUTUBE UPLOAD
# ==========================================
def upload_to_youtube_lightweight(video_path, metadata, category_id="24"): # 24 is Entertainment
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    token_url = get_safe_url("aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4=")
    res = requests.post(token_url, data={
        "client_id": os.environ.get("CLIENT_ID"),
        "client_secret": os.environ.get("CLIENT_SECRET"),
        "refresh_token": os.environ.get("REFRESH_TOKEN"),
        "grant_type": "refresh_token"
    })
    if res.status_code != 200:
        print("❌ Token Error:", res.text)
        return
    access_token = res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(os.path.getsize(video_path)),
        "X-Upload-Content-Type": "video/mp4"
    }
    body = {
        "snippet": {"title": metadata['title'][:100], "description": metadata['description'], "tags": metadata['tags'], "categoryId": category_id},
        "status": {"privacyStatus": "public"} 
    }
    upload_url = get_safe_url("aHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vdXBsb2FkL3lvdXR1YmUvdjMvdmlkZW9zP3VwbG9hZFR5cGU9cmVzdW1hYmxlJnBhcnQ9c25pcHBldCxzdGF0dXM=")
    init_res = requests.post(upload_url, headers=headers, json=body)
    location = init_res.headers.get("Location")
    if not location:
        print("❌ Upload Init Failed:", init_res.text)
        return
    print("⏳ Pushing video data...")
    with open(video_path, "rb") as f:
        upload_res = requests.put(location, headers={"Authorization": f"Bearer {access_token}"}, data=f)
    if upload_res.status_code in [200, 201]:
        yt_base = get_safe_url("aHR0cHM6Ly95b3V0dS5iZS8=")
        print(f"🎉 SUCCESS! Video Live: {yt_base}{upload_res.json().get('id')}")
    else:
        print(f"❌ Upload Failed: {upload_res.text}")

# ==========================================
# 7. MAIN WORKFLOW
# ==========================================
def main():
    if not all(os.environ.get(k) for k in ["GEMINI_API_KEY", "CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN"]):
        print("❌ Missing API Keys in Environment Variables!")
        return

    print("🚀 Starting Shayari Shorts Bot...")
    shayari_data = get_shayari_from_gemini()

    if shayari_data:
        print("✅ Gemini successfully generated Shayari! Initiating Video...")
        font_path = download_font()
        bg_music = download_sad_bgm()
        
        parts_data = []
        for slide in shayari_data['slides']:
            parts_data.append({
                "text": slide['narration'], 
                "slide_data": slide, 
                "font_path": font_path
            })

        video_path = assemble_final_video(parts_data, bg_music=bg_music)
        
        # Category 24 is Entertainment, which fits Shayari well
        upload_to_youtube_lightweight(video_path, shayari_data['metadata'], category_id="24")
        print("✅ Shayari Shorts Workflow Complete!")

    else:
        print("⚠️ Gemini couldn't generate data.")

if __name__ == "__main__":
    main()
