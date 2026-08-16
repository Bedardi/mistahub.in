import os
import sys
import subprocess

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
import json
import random
import urllib.parse
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_font():
    font_path = "BoldFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading Font for Slides...")
        # Direct stable link to Google's Roboto Black font
        url = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Black.ttf"
        try:
            res = requests.get(url, headers=get_fake_headers(), timeout=15)
            if res.status_code == 200:
                with open(font_path, 'wb') as f: f.write(res.content)
        except Exception as e:
            print(f"⚠️ Font download failed: {e}")
            
    return font_path if os.path.exists(font_path) else None

def download_background_music():
    print("🎵 Downloading Ambient BGM...")
    url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_5116fc01c1.mp3?filename=dark-ambient-107774.mp3"
    music_path = "ambient_bg.mp3"
    try:
        res = requests.get(url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f: f.write(res.content)
    except: pass
    return music_path if os.path.exists(music_path) else None

def call_gemini(prompt):
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.8}}
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            data = res.json()
            if res.status_code == 200 and 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except: pass
    return ""

def generate_pollinations_image(prompt, filename):
    print(f"🎨 Generating AI Image via Pollinations: {filename}...")
    safe_prompt = urllib.parse.quote("Dark cinematic mystery horror realistic, " + prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open(filename, 'wb') as f: f.write(res.content)
            return filename
    except: pass
    img = Image.new('RGB', (1920, 1080), color=(15, 15, 15))
    img.save(filename)
    return filename

async def generate_tts(text, filename):
    await edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+3%").save(filename)

# ==========================================
# 3. GEMINI DIRECT JOB GENERATOR
# ==========================================

def get_job_vacancy_from_gemini():
    print("🔍 Asking Gemini AI for Latest Job Vacancy...")
    
    past_jobs = ""
    if os.path.exists("posted_jobs.txt"):
        with open("posted_jobs.txt", "r") as f:
            past_jobs = f.read()

    # EMOJIS REMOVED FROM PROMPT TO PREVENT CRASHES!
    prompt = f"""
    You are an expert YouTube Education Job Updates Creator. 
    Provide details for a popular Indian Government or Top Private Sector Job Vacancy (like SSC, Railway, Bank, UPSC, Defence) expected or currently active in 2026.
    
    CRITICAL RULE 1: DO NOT use any of these jobs that I have already covered: {past_jobs}
    CRITICAL RULE 2: STRICTLY DO NOT USE ANY EMOJIS in the JSON output. Keep text clean and plain.
    
    Generate JSON exactly in this format. The narration must be an engaging Hinglish voiceover script for that specific slide.
    {{
      "metadata": {{
        "title": "[Job Name] Recruitment 2026 | Eligibility, Age, Salary | Full Details",
        "description": "Full details about this new job vacancy...",
        "tags": ["sarkari naukri", "job update", "education", "latest jobs", "2026 jobs"],
        "job_name_for_database": "[Short Job Name, e.g., SSC CGL]"
      }},
      "slides": [
        {{"title": "NEW VACANCY OUT", "points": ["Post: [Job Name]", "Total Vacancies: [Number]"], "narration": "Namaskar dosto, aaj ek bahut badi vacancy aayi hai..."}},
        {{"title": "IMPORTANT DATES", "points": ["Start Date: [Date]", "Last Date: [Date]"], "narration": "Form bharne ki tarikh shuru ho rahi hai..."}},
        {{"title": "FEES & SALARY", "points": ["Gen/OBC Fee: [Amount]", "Salary: [Amount]"], "narration": "Fees ki baat karein toh..."}},
        {{"title": "ELIGIBILITY", "points": ["Age Limit: [Age]", "Qualification: [Qualification]"], "narration": "Eligibility criteria me..."}}
      ]
    }}
    """
    
    response = call_gemini(prompt)
    if response.startswith("```json"): response = response[7:-3]
    
    try:
        data = json.loads(response.strip())
        return data
    except Exception as e:
        print(f"⚠️ Gemini failed to generate proper Job JSON: {e}")
        return None

def generate_job_slide_image(slide_data, font_path, slide_index):
    w, h = 1920, 1080
    img = Image.new('RGB', (w, h), color=(15, 32, 39)) 
    draw = ImageDraw.Draw(img)
    
    try: title_font = ImageFont.truetype(font_path, 90)
    except: title_font = ImageFont.load_default()
    
    try: text_font = ImageFont.truetype(font_path, 60)
    except: text_font = ImageFont.load_default()

    # Clean text function to ensure no stray characters crash PIL
    def safe_text(txt): return txt.encode('ascii', 'ignore').decode('ascii')

    title_text = safe_text(slide_data.get('title', 'UPDATE'))
    draw.text((100, 150), title_text, font=title_font, fill=(255, 215, 0))
    draw.line([(100, 260), (1000, 260)], fill=(255, 215, 0), width=8)

    y_pos = 350
    for point in slide_data.get('points', []):
        pt_text = safe_text(point)
        # Using ">> " instead of "👉 " to avoid Unicode errors
        draw.text((100, y_pos), f">>  {pt_text}", font=text_font, fill=(240, 240, 240))
        y_pos += 120

    filename = f"job_slide_{slide_index}.png"
    img.save(filename)
    return filename

# ==========================================
# 4. AUDIOBOOK MODULE (Fallback)
# ==========================================
def generate_audiobook_chapter_data(ch):
    print(f"📖 Expanding Chapter {ch['chapter_num']}: {ch['topic']}...")
    prompt = f"Write Chapter {ch['chapter_num']} ({ch['topic']}) for a long Hinglish audiobook. Requirement: suspenseful. Length: 800-1000 words. Output ONLY narration without any headers."
    narration = call_gemini(prompt)
    return {"topic": ch['topic'], "text": narration}

# ==========================================
# 5. FFMPEG VIDEO ASSEMBLY
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

def assemble_final_video(parts_data, bg_music=None, is_job=False):
    print("🎬 Starting FFmpeg Assembly...")
    video_files = []

    for idx, part in enumerate(parts_data):
        audio_file = f"temp_audio_{idx}.mp3"
        vid_file = f"temp_part_{idx}.mp4"
        
        asyncio.run(generate_tts(part['text'], audio_file))
        
        if is_job:
            img_file = generate_job_slide_image(part['slide_data'], part['font_path'], idx)
        else:
            img_file = f"temp_img_{idx}.jpg"
            generate_pollinations_image(part['topic'], img_file)

        build_chapter_video(img_file, audio_file, vid_file)
        video_files.append(vid_file)

    print("🔗 Concatenating All Parts...")
    with open("concat.txt", "w") as f:
        for vid in video_files:
            f.write(f"file '{vid}'\n")

    merged_vid = "merged_no_bgm.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", merged_vid], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    final_output = "final_ready_video.mp4"
    if bg_music and os.path.exists(bg_music):
        print("🎧 Adding Ambient Background Music...")
        cmd = [
            "ffmpeg", "-y", "-i", merged_vid, "-stream_loop", "-1", "-i", bg_music,
            "-filter_complex", "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
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
            os.remove(f"temp_part_{i}.mp4")
            if is_job: os.remove(f"job_slide_{i}.png")
            else: os.remove(f"temp_img_{i}.jpg")
        if os.path.exists("merged_no_bgm.mp4"): os.remove("merged_no_bgm.mp4")
    except: pass

    return final_output

# ==========================================
# 6. YOUTUBE UPLOAD (Fixed URL)
# ==========================================
def upload_to_youtube_lightweight(video_path, metadata, category_id="24"):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    
    token_url = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
    
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

    upload_url = "[https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status](https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status)"
    init_res = requests.post(upload_url, headers=headers, json=body)

    location = init_res.headers.get("Location")
    if not location:
        print("❌ Upload Init Failed:", init_res.text)
        return

    print("⏳ Pushing video data...")
    with open(video_path, "rb") as f:
        upload_res = requests.put(location, headers={"Authorization": f"Bearer {access_token}"}, data=f)

    if upload_res.status_code in [200, 201]:
        print(f"🎉 SUCCESS! Video Live: [https://youtu.be/](https://youtu.be/){upload_res.json().get('id')}")
    else:
        print(f"❌ Upload Failed: {upload_res.text}")

# ==========================================
# 7. MAIN WORKFLOW
# ==========================================
def main():
    if not all(os.environ.get(k) for k in ["GEMINI_API_KEY", "CLIENT_ID", "CLIENT_SECRET", "REFRESH_TOKEN"]):
        print("❌ Missing API Keys in Environment Variables!")
        return

    print("🚀 Starting Fully Automated Creator Bot...")
    
    job_data = get_job_vacancy_from_gemini()
    
    if job_data:
        print("✅ Gemini successfully generated a Job Vacancy! Initiating Education Video...")
        font_path = download_font()
        
        parts_data = []
        for slide in job_data['slides']:
            parts_data.append({
                "text": slide['narration'], 
                "slide_data": slide,
                "font_path": font_path
            })
            
        video_path = assemble_final_video(parts_data, bg_music=None, is_job=True)
        upload_to_youtube_lightweight(video_path, job_data['metadata'], category_id="27")
        
        job_name = job_data['metadata'].get('job_name_for_database', 'Unknown Job')
        with open("posted_jobs.txt", "a") as f:
            f.write(f"{job_name}\n")
            
        print("✅ Education Job Workflow Complete!")
        
    else:
        print("⚠️ Gemini couldn't generate a Job. Falling back to Audiobook Generator...")
        bg_music = download_background_music()

        prompt = """Create an outline for a Hinglish Mystery Horror story. Divide into 5 Chapters. Output JSON ONLY:
        {"metadata": {"title": "Unsolved Mystery - Hindi Audiobook", "description": "Listen to this gripping story. #audiobook #hindi", "tags": ["audiobook", "hindi story", "thriller"]}, "chapters": [{"chapter_num": 1, "topic": "The Strange Discovery"}, {"chapter_num": 2, "topic": "Shadows"}, {"chapter_num": 3, "topic": "Darkness"}, {"chapter_num": 4, "topic": "Secret"}, {"chapter_num": 5, "topic": "Final Truth"}]}"""

        raw = call_gemini(prompt)
        if raw.startswith("```json"): raw = raw[7:-3]
        script_data = json.loads(raw.strip())

        with ThreadPoolExecutor(max_workers=5) as executor:
            expanded_chapters = list(executor.map(generate_audiobook_chapter_data, script_data['chapters']))

        video_path = assemble_final_video(expanded_chapters, bg_music=bg_music, is_job=False)
        upload_to_youtube_lightweight(video_path, script_data['metadata'], category_id="24")
        
    print("✅ Full Process Finished!")

if __name__ == "__main__":
    main()
