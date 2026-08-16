import os
import requests
import json
import urllib.parse
import time
import random
import textwrap
import asyncio
import base64
import edge_tts
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

# MoviePy for Video Assembly
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, 
    concatenate_videoclips
)
from moviepy.audio.fx.all import volumex

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def get_url(b64_string):
    return base64.b64decode(b64_string).decode("utf-8")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

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
    print("🎵 Downloading Ambient Audio...")
    music_url = get_url("aHR0cHM6Ly9jZG4ucGl4YWJheS5jb20vZG93bmxvYWQvYXVkaW8vMjAyMi8wMy8xNS9hdWRpb181MTE2ZmMwMWMxLm1wMz9maWxlbmFtZT1kYXJrLWFtYmllbnQtMTA3Nzc0Lm1wMw==")
    music_path = "ambient_bg.mp3"
    try:
        res = requests.get(music_url, headers=get_fake_headers(), timeout=15)
        if res.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(res.content)
    except Exception as e:
        print(f"⚠️ Background music skipped: {e}")
    return music_path if os.path.exists(music_path) else None

def call_gemini(prompt):
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7}
        }
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
            data = res.json()
            if res.status_code == 200 and 'candidates' in data:
                print(f"✅ Gemini API Success using model: {model}")
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            pass
    raise Exception("❌ All Gemini API Models failed. Please verify your GEMINI_API_KEY.")

async def generate_tts_file(text, filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+2%")
    await communicate.save(filename)

# ==========================================
# JOB VACANCY MODULE (NEW)
# ==========================================
def get_latest_job_link():
    print("🔍 Checking for New Job Vacancies...")
    try:
        url = "https://www.sarkariresult.com/latestjob.php"
        res = requests.get(url, headers=get_fake_headers(), timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        post_div = soup.find('div', id='post')
        if post_div:
            first_link = post_div.find('a')
            if first_link and 'href' in first_link.attrs:
                job_url = first_link['href']
                
                # Check history automatically (Script creates file if not exists)
                if os.path.exists("posted_jobs.txt"):
                    with open("posted_jobs.txt", "r") as f:
                        if job_url in f.read():
                            print("⏭️ Video already made for this vacancy. Skipping to Audiobook.")
                            return None
                return job_url
    except Exception as e:
        print(f"⚠️ Job Scraper Error: {e}")
    return None

def fetch_and_parse_job_data(job_url):
    print(f"📄 Fetching details from: {job_url}")
    try:
        res = requests.get(job_url, headers=get_fake_headers(), timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        page_text = soup.get_text(separator="\n", strip=True)[:6000]
        
        prompt = f"""
        You are an expert YouTube Education & Job Updates Creator.
        Analyze this raw webpage text for a new Job Vacancy and extract details.
        
        Webpage Text:
        {page_text}
        
        Generate a JSON exactly in this format:
        {{
          "metadata": {{
            "title": "[Job Name] Recruitment 2026 | Eligibility, Age, Salary | Full Details",
            "description": "Full details about this new job vacancy... Apply link etc.",
            "tags": ["sarkari naukri", "job update", "latest jobs 2026", "education"]
          }},
          "slides": [
            {{"title": "🚨 NEW VACANCY OUT", "points": ["Job/Post Name", "Total Vacancies: XYZ"]}},
            {{"title": "📅 IMPORTANT DATES", "points": ["Start Date: XYZ", "Last Date: XYZ"]}},
            {{"title": "💰 FEES & SALARY", "points": ["Gen/OBC Fee: XYZ", "SC/ST Fee: XYZ", "Salary: XYZ"]}},
            {{"title": "🎓 ELIGIBILITY", "points": ["Age Limit: XYZ", "Qualification: XYZ"]}}
          ],
          "script": "Namaskar dosto! Aaj ek bahut badi vacancy nikal kar aayi hai... (Write a highly engaging Hindi/Hinglish YouTube voiceover script explaining all details clearly. Length ~300-400 words.)"
        }}
        """
        response = call_gemini(prompt)
        if response.startswith("```json"): response = response[7:-3]
        return json.loads(response), job_url
    except Exception as e:
        print(f"⚠️ Failed to parse job data: {e}")
        return None, None

def generate_slide_image(slide_data, font_path, slide_index):
    w, h = 1920, 1080
    img = Image.new('RGB', (w, h), color=(15, 32, 39)) 
    draw = ImageDraw.Draw(img)
    
    try: title_font = ImageFont.truetype(font_path, 90)
    except: title_font = ImageFont.load_default()
    
    try: text_font = ImageFont.truetype(font_path, 60)
    except: text_font = ImageFont.load_default()

    title = slide_data['title']
    draw.text((100, 150), title, font=title_font, fill=(255, 215, 0))
    draw.line([(100, 260), (1000, 260)], fill=(255, 215, 0), width=8)

    y_pos = 350
    for point in slide_data['points']:
        draw.text((100, y_pos), f"👉 {point}", font=text_font, fill=(240, 240, 240))
        y_pos += 120

    filename = f"slide_{slide_index}.png"
    img.save(filename)
    return filename

def build_job_video(data, font_path):
    print("⚡ Building Dynamic Job Update Video...")
    
    audio_file = "job_audio.mp3"
    asyncio.run(generate_tts_file(data['script'], audio_file))
    voice_clip = AudioFileClip(audio_file)
    total_duration = voice_clip.duration
    
    slide_duration = total_duration / len(data['slides'])
    
    clips = []
    slide_files = []
    for i, slide in enumerate(data['slides']):
        img_path = generate_slide_image(slide, font_path, i)
        slide_files.append(img_path)
        clip = ImageClip(img_path).set_duration(slide_duration).resize(lambda t: 1 + 0.005 * t).set_position('center')
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose").set_audio(voice_clip)
    output_filename = "job_update_video.mp4"
    
    print("🎬 Rendering Job Update MP4...")
    video.write_videofile(output_filename, fps=15, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
    
    try: os.remove(audio_file)
    except: pass
    for f in slide_files:
        try: os.remove(f)
        except: pass
        
    return output_filename

# ==========================================
# AUDIOBOOK MODULE (FALLBACK)
# ==========================================
def generate_dark_canvas_image(title_text, font_path):
    print("🎨 Creating Dark Aesthetic Artwork...")
    w, h = 1920, 1080
    img = Image.new('RGB', (w, h), color=(12, 12, 18))
    draw = ImageDraw.Draw(img)

    try: font = ImageFont.truetype(font_path, 65)
    except: font = ImageFont.load_default()

    wrapped_lines = textwrap.wrap(title_text, width=40)
    total_h = len(wrapped_lines) * 80
    y = (h - total_h) // 2

    for line in wrapped_lines:
        try: bbox = draw.textbbox((0, 0), line, font=font); line_w = bbox[2] - bbox[0]
        except: line_w = font.getlength(line)
        x = (w - line_w) // 2
        draw.text((x, y), line, font=font, fill=(240, 240, 240), stroke_width=3, stroke_fill=(0, 0, 0))
        y += 80

    img.save("audiobook_cover.png")
    return "audiobook_cover.png"

def generate_long_audiobook_script():
    print("🧠 Outlining Long 20-50 Minute Story via Gemini API...")
    genres = ["Mystery Horror Thriller", "Dark Psychology Secrets", "Historical Secret Files", "Psychological Crime Thriller"]
    selected_genre = random.choice(genres)
    
    outline_prompt = f"""
    You are a viral YouTube Audiobook Creator. Create an outline for a long 20-30 minute Hindi/Hinglish story in '{selected_genre}'.
    Divide the story into 5 sequential Chapters.
    Output JSON ONLY:
    {{
      "metadata": {{
        "title": "Unsolved Mystery - Hindi Full Audiobook Story",
        "description": "Listen to this long gripping audiobook story in Hindi. #audiobook #hindi #story #mystery",
        "tags": ["audiobook", "hindi story", "thriller", "full story"]
      }},
      "chapters": [
        {{"chapter_num": 1, "topic": "The Strange Discovery"}},
        {{"chapter_num": 2, "topic": "The Unseen Shadows"}},
        {{"chapter_num": 3, "topic": "Deeper Into The Darkness"}},
        {{"chapter_num": 4, "topic": "The Shocking Secret"}},
        {{"chapter_num": 5, "topic": "Final Truth Revealed"}}
      ]
    }}
    """
    outline_raw = call_gemini(outline_prompt)
    if outline_raw.startswith("```json"): outline_raw = outline_raw[7:-3]
    script_data = json.loads(outline_raw.strip())

    full_story_parts = []
    for ch in script_data['chapters']:
        print(f"📖 Expanding Chapter {ch['chapter_num']}: {ch['topic']}...")
        chapter_prompt = f"""
        Write Chapter {ch['chapter_num']} ({ch['topic']}) for a long storytelling audiobook in Hindi (written in Hinglish Roman Script).
        Requirement: Make it extremely detailed, suspenseful, slow-paced, atmospheric, and descriptive.
        Target length: 800 to 1200 words for this chapter alone.
        Output ONLY the narration story text, no titles or notes.
        """
        narration = call_gemini(chapter_prompt)
        full_story_parts.append(narration)

    script_data['full_narration'] = "\n\n".join(full_story_parts)
    return script_data

def build_long_audiobook_video(data, font_path, bg_music_path):
    print("⚡ Building Long Video & Rendering...")
    audio_file = "full_story_audio.mp3"
    print("🗣️ Generating Full Voiceover Audio...")
    asyncio.run(generate_tts_file(data['full_narration'], audio_file))

    voice_clip = AudioFileClip(audio_file)
    total_duration = voice_clip.duration
    print(f"⏱️ Total Video Duration Generated: {round(total_duration / 60, 2)} Minutes!")

    bg_img_path = generate_dark_canvas_image(data['metadata']['title'], font_path)
    
    bg_clip = ImageClip(bg_img_path).resize(width=1920, height=1080).set_duration(total_duration)
    bg_clip = bg_clip.resize(lambda t: 1 + 0.002 * t).set_position('center')

    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path)
        if bg_music.duration < total_duration:
            bg_music = bg_music.loop(duration=total_duration)
        else:
            bg_music = bg_music.subclip(0, total_duration)

        bg_music = volumex(bg_music, 0.08)
        from moviepy.audio.AudioClip import CompositeAudioClip
        final_audio = CompositeAudioClip([voice_clip, bg_music])
    else:
        final_audio = voice_clip

    final_video = CompositeVideoClip([bg_clip]).set_audio(final_audio)
    output_filename = "long_audiobook_video.mp4"
    
    print("🎬 Rendering Final Long MP4 Video...")
    final_video.write_videofile(
        output_filename, fps=15, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None
    )
    
    try: 
        os.remove(audio_file)
        os.remove(bg_img_path)
    except: pass
    return output_filename

# ==========================================
# UPLOADER MODULE
# ==========================================
def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading Video to YouTube: {metadata['title']}")
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
                "tags": metadata['tags'][:15], 
                "categoryId": "27" # 27 is Education, 24 is Entertainment
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        }
        req = youtube.videos().insert(
            part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )
        response = req.execute()
        print(f"🎉 SUCCESS! Video Uploaded! ID: {response['id']}")
    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

# ==========================================
# MAIN WORKFLOW
# ==========================================
def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY Missing!")
        return

    print("🚀 Starting Smart YouTube Automation...")
    font_path = download_font()
    
    # 1. Check for New Job Vacancies first
    job_link = get_latest_job_link()
    job_data = None
    
    if job_link:
        job_data, tracked_url = fetch_and_parse_job_data(job_link)
    
    # 2. DECISION LOGIC
    if job_data:
        print("✅ New Job Found! Initiating Education Video...")
        video_path = build_job_video(job_data, font_path)
        metadata = job_data['metadata']
        
        # Save link automatically so we don't repeat it
        with open("posted_jobs.txt", "a") as f:
            f.write(f"{tracked_url}\n")
            
    else:
        print("⚠️ No New Jobs found (or already covered). Falling back to Audiobook!")
        bg_music_path = download_background_music()
        data = generate_long_audiobook_script()
        video_path = build_long_audiobook_video(data, font_path, bg_music_path)
        metadata = data['metadata']

    # 3. Upload Output
    upload_to_youtube(video_path, metadata)
    
    # Optional: Clean up the generated videos after successful upload
    try:
        os.remove(video_path)
    except:
        pass
        
    print("✅ Workflow Complete!")

if __name__ == "__main__":
    main()
