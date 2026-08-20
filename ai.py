import os
import sys
import subprocess
import base64
import json
import urllib.parse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ==========================================
# 1. AUTO-INSTALLER
# ==========================================
def install_packages():
    print("⚙️ Checking dependencies...")
    try:
        import requests
        import edge_tts
        from PIL import Image
    except ImportError:
        print("📦 Installing required packages automatically...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "edge-tts", "pillow"])
        print("✅ Packages installed successfully!\n")

install_packages()

import requests
import edge_tts
from PIL import Image

# IMPORTANT: SET YOUR API KEYS HERE OR IN ENVIRONMENT VARIABLES
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_KEY_HERE")
CLIENT_ID = os.environ.get("CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID_HERE")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET_HERE")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN", "YOUR_GOOGLE_REFRESH_TOKEN_HERE")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_safe_url(b64_string):
    return base64.b64decode(b64_string).decode("utf-8")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_sad_bgm():
    print("🎵 Downloading Sad BGM...")
    url = get_safe_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8xMC8yNS9hdWRpb18yM2I0NjIyZjVlLm1wMz9maWxlbmFtZT1zYWQtY2luZW1hdGljLXBpYW5vLTEyMzk3MC5tcDM=")
    music_path = "sad_bg.mp3"
    try:
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f: f.write(res.content)
            return music_path
    except: pass
    return None

def generate_pollinations_image_vertical(prompt, filename):
    print(f"🎨 Generating AI Background: {filename}...")
    safe_prompt = urllib.parse.quote("Cinematic, moody, aesthetic, lonely, 4k, " + prompt)
    base_img = get_safe_url("aHR0cHM6Ly9pbWFnZS5wb2xsaW5hdGlvbnMuYWkvcHJvbXB0Lw==")
    url = f"{base_img}{safe_prompt}?width=1080&height=1920&nologo=true"

    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(filename, 'wb') as f: f.write(res.content)
            return filename
    except: pass
    # Fallback to dark screen if image gen fails
    img = Image.new('RGB', (1080, 1920), color=(20, 20, 25))
    img.save(filename)
    return filename

def call_gemini(prompt):
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
    base_api = get_safe_url("aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL21vZGVscy8=")

    for model in models:
        url = f"{base_api}{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.85}} 
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            data = res.json()
            if res.status_code == 200 and 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except: pass
    return ""

# ==========================================
# 3. AI SCRIPT GENERATOR (VIRAL KADWA SACH)
# ==========================================
def get_viral_quotes_from_gemini():
    print("🔍 Asking Gemini AI for Viral 'Kadwa Sach' Script...")
    prompt = """
    Write a highly shareable, emotional 15-20 second YouTube Short script in Hindi (written in Hinglish).
    Topic: Bitter truth about life, fake friends, or money.
    
    Structure:
    Slide 1: Hook (e.g., "Zindagi ka ek kadwa sach bataun?")
    Slide 2: Core thought (Deep and relatable).
    
    CRITICAL: NO EMOJIS in JSON. Output ONLY valid JSON.
    
    Format:
    {
      "metadata": {
        "title": "Zindagi Ka Kadwa Sach 💔 #shorts #quotes", 
        "description": "Deep truth #emotional #kadwasach #hindi", 
        "tags": ["shorts", "quotes", "emotional", "deep quotes", "hindi", "kadwa sach"]
      },
      "slides": [
        {"visual_prompt": "cinematic dark empty street", "narration": "Zindagi ka ek sach bataun?"},
        {"visual_prompt": "dark aesthetic moody room", "narration": "Log sath tab tak dete hain, jab tak unka matlab hota hai."}
      ]
    }
    """
    response = call_gemini(prompt)
    if response.startswith("```json"): response = response[7:-3]
    try: return json.loads(response.strip())
    except Exception as e:
        print(f"❌ Gemini JSON Error: {e}")
        return None

# ==========================================
# 4. AUDIO & SUBTITLE GENERATOR
# ==========================================
async def generate_tts_with_subs(text, audio_filename, vtt_filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-10%", pitch="-5Hz")
    subs = []

    with open(audio_filename, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                offset_sec = chunk["offset"] / 10_000_000.0
                duration_sec = chunk["duration"] / 10_000_000.0
                
                # Format to VTT Timestamp (HH:MM:SS.mmm)
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
# 5. VIDEO ASSEMBLY (FFMPEG)
# ==========================================
def build_chapter_video(image_path, audio_path, vtt_path, output_path):
    print(f"⚡ Rendering slide: {output_path}...")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles={vtt_path}:force_style='FontSize=26,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Shadow=2,Alignment=2,MarginV=150'",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def assemble_final_video(parts_data, bg_music=None):
    print("🎬 Assembling Final Short Video...")
    video_files = []

    for idx, part in enumerate(parts_data):
        audio_file = f"temp_audio_{idx}.mp3"
        vtt_file = f"temp_sub_{idx}.vtt"
        vid_file = f"temp_part_{idx}.mp4"

        asyncio.run(generate_tts_with_subs(part['text'], audio_file, vtt_file))
        img_file = generate_pollinations_image_vertical(part['slide_data']['visual_prompt'], f"temp_img_{idx}.jpg")
        
        build_chapter_video(img_file, audio_file, vtt_file, vid_file)
        video_files.append(vid_file)

    with open("concat.txt", "w") as f:
        for vid in video_files: f.write(f"file '{vid}'\n")

    merged_vid = "merged_no_bgm.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", merged_vid], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    final_output = f"Short_{datetime.now().strftime('%Y%m%d_%H%M')}.mp4"
    
    if bg_music and os.path.exists(bg_music):
        print("🎧 Adding Emotional BGM...")
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
        if os.path.exists("merged_no_bgm.mp4"): os.remove("merged_no_bgm.mp4")
        for i in range(len(parts_data)):
            for ext in ['mp3', 'vtt', 'mp4', 'jpg']:
                file_to_del = f"temp_{ext[:-1] if ext!='mp4' else 'part'}_{i}.{ext}"
                if os.path.exists(file_to_del): os.remove(file_to_del)
    except: pass

    return final_output

# ==========================================
# 6. YOUTUBE UPLOAD (FIXED & BULLETPROOF)
# ==========================================
def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading to YouTube...")
    
    # Ensure Title contains #shorts
    title = metadata.get('title', 'Zindagi Ka Sach 💔')
    if '#shorts' not in title.lower():
        title = f"{title} #shorts"
    title = title[:100] # Max length is 100

    description = metadata.get('description', '')
    tags = metadata.get('tags', ['shorts', 'quotes'])

    # 1. Get Access Token
    token_url = get_safe_url("aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4=")
    res = requests.post(token_url, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    })
    
    if res.status_code != 200:
        print(f"❌ Auth Error: Check your Client ID/Secret/Refresh Token.\nDetails: {res.text}")
        return False
        
    access_token = res.json()["access_token"]
    
    # 2. Initialize Upload (Resumable Session)
    upload_url = "[https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status](https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status)"
    
    headers_init = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(os.path.getsize(video_path)),
        "X-Upload-Content-Type": "video/mp4"
    }
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24" # 24 = Entertainment
        },
        "status": {
            "privacyStatus": "public", # Use 'private' for testing if you want
            "selfDeclaredMadeForKids": False
        }
    }
    
    print("⏳ Getting upload URL...")
    init_res = requests.post(upload_url, headers=headers_init, json=body)
    
    if init_res.status_code != 200:
        print(f"❌ Upload Init Failed: {init_res.text}")
        return False
        
    upload_location = init_res.headers.get("Location")
    if not upload_location:
        print("❌ Could not get upload location URL.")
        return False

    # 3. Actually Upload the Video File
    print(f"📡 Pushing video file ({os.path.getsize(video_path)} bytes)...")
    with open(video_path, "rb") as f:
        headers_upload = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "video/mp4"
        }
        upload_res = requests.put(upload_location, headers=headers_upload, data=f)
        
    if upload_res.status_code in [200, 201]:
        yt_id = upload_res.json().get('id')
        yt_base = get_safe_url("aHR0cHM6Ly95b3V0dS5iZS8=")
        print("\n" + "="*50)
        print(f"🎉 SUCCESS! Video is LIVE on YouTube!")
        print(f"🔗 Link: {yt_base}{yt_id}")
        print("="*50 + "\n")
        return True
    else:
        print(f"❌ Video Upload Failed: Status {upload_res.status_code}")
        print(f"Details: {upload_res.text}")
        return False

# ==========================================
# 7. MAIN WORKFLOW
# ==========================================
def main():
    if GEMINI_API_KEY == "YOUR_GEMINI_KEY_HERE" or CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID_HERE":
        print("⚠️ STOP: You must enter your API Keys at the top of the code before running.")
        return

    print("🚀 Starting MistaHub Shorts Automation...")
    quotes_data = get_viral_quotes_from_gemini()

    if quotes_data and 'slides' in quotes_data:
        bg_music = download_sad_bgm()
        
        parts_data = []
        for slide in quotes_data['slides']:
            parts_data.append({
                "text": slide['narration'], 
                "slide_data": slide
            })

        video_path = assemble_final_video(parts_data, bg_music=bg_music)
        print(f"✅ Video generated successfully: {video_path}")
        
        # Uncomment this line if you want to skip upload while testing
        upload_to_youtube(video_path, quotes_data['metadata'])
        
    else:
        print("⚠️ Failed to generate content from Gemini.")

if __name__ == "__main__":
    main()
