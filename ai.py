import os
import sys
import subprocess

# ==========================================
# 1. AUTO-INSTALLER (NO requirements.txt NEEDED)
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

# Dependencies load karne ke baad import
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
# 2. HELPER FUNCTIONS & AI GENERATORS
# ==========================================

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_background_music():
    print("🎵 Downloading Ambient BGM...")
    url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_5116fc01c1.mp3?filename=dark-ambient-107774.mp3"
    music_path = "ambient_bg.mp3"
    try:
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f: f.write(res.content)
    except:
        pass
    return music_path if os.path.exists(music_path) else None

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.85}}
    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    data = res.json()
    if res.status_code == 200 and 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text'].strip()
    return ""

def generate_pollinations_image(prompt, filename):
    print(f"🎨 Generating AI Image via Pollinations: {filename}...")
    # Safe fallback if Gemini prompt is weird
    safe_prompt = urllib.parse.quote("Dark cinematic mystery horror realistic, " + prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(res.content)
            return filename
    except Exception as e:
        print(f"⚠️ Image generation failed for {filename}: {e}")
    
    # Fallback to black screen if Pollinations fails
    img = Image.new('RGB', (1920, 1080), color=(15, 15, 15))
    img.save(filename)
    return filename

def generate_chapter_data(ch):
    print(f"📖 Expanding Chapter {ch['chapter_num']}: {ch['topic']}...")
    prompt = f"Write Chapter {ch['chapter_num']} ({ch['topic']}) for a long Hinglish audiobook. Requirement: suspenseful. Length: 800-1000 words. Output ONLY narration without any headers."
    narration = call_gemini(prompt)
    return {"num": ch['chapter_num'], "topic": ch['topic'], "text": narration}

async def generate_tts(text, filename):
    await edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+5%").save(filename)

# ==========================================
# 3. VIDEO ASSEMBLY (FFMPEG NATIVE)
# ==========================================

def build_chapter_video(image_path, audio_path, output_path):
    print(f"⚡ Rendering {output_path} (Image + Audio)...")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "1", "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def build_full_movie(chapters_data, bg_music):
    print("🎬 Starting FFmpeg Chapter Assembly...")
    chapter_files = []
    
    # Generate Audio, Images, and Mini-videos for each chapter
    for ch in chapters_data:
        num = ch['num']
        audio_file = f"audio_{num}.mp3"
        img_file = f"img_{num}.jpg"
        vid_file = f"chap_{num}.mp4"
        
        asyncio.run(generate_tts(ch['text'], audio_file))
        generate_pollinations_image(ch['topic'], img_file)
        build_chapter_video(img_file, audio_file, vid_file)
        
        chapter_files.append(vid_file)
    
    # Merge all chapter videos into one
    print("🔗 Concatenating All Chapters...")
    with open("concat.txt", "w") as f:
        for vid in chapter_files:
            f.write(f"file '{vid}'\n")
            
    merged_vid = "merged_no_bgm.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", merged_vid], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    # Add Background Music (if available)
    final_output = "long_audiobook_final.mp4"
    if bg_music and os.path.exists(bg_music):
        print("🎧 Adding Ambient Background Music...")
        cmd = [
            "ffmpeg", "-y", 
            "-i", merged_vid, 
            "-stream_loop", "-1", "-i", bg_music,
            "-filter_complex", "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]", 
            "-c:v", "copy", "-c:a", "aac", final_output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        os.rename(merged_vid, final_output)
        
    print("🧹 Cleaning up temp files...")
    try:
        os.remove("concat.txt")
        for i in range(1, 6):
            os.remove(f"audio_{i}.mp3")
            os.remove(f"img_{i}.jpg")
            os.remove(f"chap_{i}.mp4")
        if os.path.exists("merged_no_bgm.mp4"): os.remove("merged_no_bgm.mp4")
    except: pass
    
    return final_output

# ==========================================
# 4. YOUTUBE UPLOAD (REST API)
# ==========================================

def upload_to_youtube_lightweight(video_path, metadata):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    res = requests.post("https://oauth2.googleapis.com/token", data={
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
        "snippet": {"title": metadata['title'][:100], "description": metadata['description'], "tags": metadata['tags'], "categoryId": "24"},
        "status": {"privacyStatus": "public"}
    }
    
    upload_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    init_res = requests.post(upload_url, headers=headers, json=body)
    
    location = init_res.headers.get("Location")
    if not location:
        print("❌ Upload Init Failed:", init_res.text)
        return

    print("⏳ Pushing video data...")
    with open(video_path, "rb") as f:
        upload_res = requests.put(location, headers={"Authorization": f"Bearer {access_token}"}, data=f)
    
    if upload_res.status_code in [200, 201]:
        print(f"🎉 SUCCESS! Video Live: https://youtu.be/{upload_res.json().get('id')}")
    else:
        print(f"❌ Upload Failed: {upload_res.text}")

# ==========================================
# 5. MAIN WORKFLOW
# ==========================================

def main():
    if not all(os.environ.get(k) for k in ["GEMINI_API_KEY", "CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN"]):
        print("❌ Missing API Keys in Environment Variables!")
        return

    print("🚀 Starting Fully Automated Audiobook Generator...")
    bg_music = download_background_music()
    
    # Get Outline from Gemini
    print("🧠 Fetching Story Outline...")
    prompt = """Create an outline for a Hinglish Mystery Horror story. Divide into 5 Chapters. Output JSON ONLY:
    {"metadata": {"title": "Unsolved Mystery - Hindi Audiobook", "description": "Listen to this gripping story. #audiobook #hindi", "tags": ["audiobook", "hindi story", "thriller"]}, "chapters": [{"chapter_num": 1, "topic": "The Strange Discovery"}, {"chapter_num": 2, "topic": "Shadows"}, {"chapter_num": 3, "topic": "Darkness"}, {"chapter_num": 4, "topic": "Secret"}, {"chapter_num": 5, "topic": "Final Truth"}]}"""
    
    raw = call_gemini(prompt)
    if raw.startswith("```json"): raw = raw[7:-3]
    script_data = json.loads(raw.strip())

    # Generate 5 Chapters Text (Fast Parallel Processing)
    with ThreadPoolExecutor(max_workers=5) as executor:
        expanded_chapters = list(executor.map(generate_chapter_data, script_data['chapters']))
        
    # Build Video and Upload
    video_path = build_full_movie(expanded_chapters, bg_music)
    upload_to_youtube_lightweight(video_path, script_data['metadata'])
    print("✅ Workflow 100% Complete!")

if __name__ == "__main__":
    main()
