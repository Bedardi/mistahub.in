import os
import requests
import json
import urllib.parse
import datetime
import time
import random
import textwrap
import base64
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

# MoviePy for Video
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip, TextClip, concatenate_audioclips
from moviepy.audio.fx.all import volumex

# YouTube API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_fake_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_font():
    font_path = "BoldFont.ttf"
    if not os.path.exists(font_path):
        print("📥 Downloading High-Impact Font...")
        url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Black.ttf"
        res = requests.get(url, headers=get_fake_headers())
        with open(font_path, 'wb') as f: 
            f.write(res.content)
    return font_path

def download_suspense_music():
    # Dark/Suspense background music for Psychology theme
    music_urls = [
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_5116fc01c1.mp3?filename=dark-ambient-107774.mp3",
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_6c97a06316.mp3?filename=suspense-113264.mp3"
    ]
    music_path = "suspense_bg.mp3"
    if not os.path.exists(music_path):
        res = requests.get(random.choice(music_urls), headers=get_fake_headers())
        with open(music_path, 'wb') as f:
            f.write(res.content)
    return music_path

def get_psychology_script():
    print(f"🧠 Generating Dark Psychology Script via Gemini...")
    
    prompt = """
    Act as a viral YouTube Shorts scriptwriter in the 'Dark Psychology & Human Behavior' niche.
    Target audience: India (Use Hinglish - A mix of Hindi in Roman English script and English words).
    
    Write a highly engaging, mysterious 3-part script. 
    Rule 1: The 'hook' must be shocking and under 3 seconds (e.g., "Kya aapko pata hai ki...").
    Rule 2: The 'body' must reveal a fascinating psychological trick or human behavior fact.
    Rule 3: The 'outro' must ask them to subscribe or comment.
    
    Generate a dark, cinematic image prompt for the background.
    Output ONLY valid JSON. Structure exactly like this:
    {
      "metadata": {
        "title": "This psychological trick is scary 🤯 #shorts #psychology",
        "description": "Learn human behavior secrets. Subscribe for more! #darkpsychology",
        "tags": ["psychology", "darkpsychology", "bodylanguage", "shorts", "facts"]
      },
      "image_prompt": "Dark mysterious silhouette of a person standing in foggy cinematic street, neon lights, 8k highly detailed",
      "hook_text": "Kya aapko pata hai ki log aapse jhooth kaise bolte hain?",
      "body_text": "Psychology kehti hai ki jab koi jhooth bolta hai, toh wo apni naak ya chehre ko baar-baar touch karta hai. Ise Pinocchio effect kehte hain.",
      "outro_text": "Apne dosto ko bhej kar unka jhooth pakdo, aur subscribe karo!"
    }
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
    
    res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload).json()
    json_text = res['candidates'][0]['content']['parts'][0]['text']
    
    if json_text.startswith("```json"): json_text = json_text[7:-3]
    return json.loads(json_text.strip())

def generate_image(prompt):
    print("🎨 Generating Cinematic Background...")
    img_path = "bg_image.jpg"
    # Using Pollinations AI as a reliable, fast fallback for GitHub actions
    encoded_prompt = urllib.parse.quote(prompt + ", dark aesthetic, mystery, 4k resolution, no text")
    url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){encoded_prompt}?width=1080&height=1920&nologo=true"
    
    res = requests.get(url, stream=True)
    with open(img_path, 'wb') as f:
        for chunk in res.iter_content(1024): f.write(chunk)
    return img_path

async def generate_ai_voice(text, filename):
    # Using Microsoft Edge TTS (Deep Male Voice)
    communicate = edge_tts.Communicate(text, "en-IN-PrabhatNeural", rate="+5%") 
    await communicate.save(filename)

def create_text_clip(text, font_path, duration, start_time):
    # Wrap text so it fits the vertical screen
    wrapped_text = "\n".join(textwrap.wrap(text, width=25))
    
    # Create text clip with stroke for readability
    txt_clip = TextClip(wrapped_text, fontsize=70, font=font_path, color='white', 
                        stroke_color='black', stroke_width=3, method='caption', 
                        size=(900, None), align='center')
    
    # Center it and set timing
    return txt_clip.set_position('center').set_start(start_time).set_duration(duration)

def build_video(data, font_path, bg_music_path, bg_img_path):
    print("⚡ Assembling Video with AI Voice and Dynamic Captions...")
    
    # 1. Generate Voice for 3 parts
    asyncio.run(generate_ai_voice(data['hook_text'], "audio_hook.mp3"))
    asyncio.run(generate_ai_voice(data['body_text'], "audio_body.mp3"))
    asyncio.run(generate_ai_voice(data['outro_text'], "audio_outro.mp3"))

    audio_hook = AudioFileClip("audio_hook.mp3")
    audio_body = AudioFileClip("audio_body.mp3")
    audio_outro = AudioFileClip("audio_outro.mp3")
    
    # Calculate durations
    t1, t2, t3 = audio_hook.duration, audio_body.duration, audio_outro.duration
    total_duration = t1 + t2 + t3
    
    # Combine Audios
    final_voice = concatenate_audioclips([audio_hook, audio_body, audio_outro])
    
    # 2. Setup Background Visuals
    bg_clip = ImageClip(bg_img_path).resize(width=1080, height=1920)
    bg_clip = bg_clip.resize(lambda t: 1 + 0.015 * t).set_position('center').set_duration(total_duration)
    
    # Add dark overlay so text pops out
    dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.6).set_duration(total_duration)
    
    # 3. Setup Dynamic Text Clips
    text_hook = create_text_clip(data['hook_text'], font_path, t1, 0)
    text_body = create_text_clip(data['body_text'], font_path, t2, t1)
    text_outro = create_text_clip(data['outro_text'], font_path, t3, t1 + t2)
    
    # 4. Mix Audio (Voice + Low Background Music)
    bg_music = AudioFileClip(bg_music_path).subclip(0, total_duration)
    bg_music = volumex(bg_music, 0.15) # Very low volume for background
    final_audio = CompositeVideoClip([bg_clip]).set_audio(final_voice) # Trick to mix audio easily
    
    # Combine everything
    final_video = CompositeVideoClip([bg_clip, dark_overlay, text_hook, text_body, text_outro])
    
    # Assign voiceover and music
    from moviepy.audio.AudioClip import CompositeAudioClip
    final_video.audio = CompositeAudioClip([final_voice, bg_music])
    
    output_filename = "viral_psychology_short.mp4"
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)
    
    # Cleanup temp files
    for f in ["audio_hook.mp3", "audio_body.mp3", "audio_outro.mp3", bg_img_path]:
        try: os.remove(f)
        except: pass
        
    return output_filename

def upload_to_youtube(video_path, metadata):
    print(f"🚀 Uploading to YouTube: {metadata['title']}")
    try:
        creds = Credentials(None, refresh_token=os.environ.get("REFRESH_TOKEN"), 
                            token_uri="[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)", 
                            client_id=os.environ.get("CLIENT_ID"), 
                            client_secret=os.environ.get("CLIENT_SECRET"))
        
        youtube = build("youtube", "v3", credentials=creds)
        
        body = {
            "snippet": {"title": metadata['title'][:100], "description": metadata['description'], "tags": metadata['tags'], "categoryId": "22"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        }
        
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, resumable=True))
        response = req.execute()
        print(f"🎉 SUCCESS! Video Live at: [https://youtube.com/shorts/](https://youtube.com/shorts/){response['id']}")
    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing in environment variables.")
        return
        
    print("🎬 Starting Dark Psychology Video Generator...")
    font_path = download_font()
    bg_music_path = download_suspense_music()
    
    data = get_psychology_script()
    bg_image_path = generate_image(data['image_prompt'])
    
    video_path = build_video(data, font_path, bg_music_path, bg_image_path)
    upload_to_youtube(video_path, data['metadata'])
    
    print("✅ Workflow Complete!")

if __name__ == "__main__":
    main()
