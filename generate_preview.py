import os
import requests
import asyncio
import urllib.parse
import random
import time
import re
import edge_tts
import datetime
import glob
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, CompositeAudioClip
from PIL import Image

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CURRENT_YEAR = datetime.datetime.now().year

def get_fake_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    fake_ip = f"{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}"
    return {"User-Agent": random.choice(user_agents), "X-Forwarded-For": fake_ip, "Client-IP": fake_ip}

async def generate_audio(text, filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-8%", pitch="-2Hz")
    await communicate.save(filename)

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers())
        with open(font_path, 'wb') as f: f.write(res.content)
    return font_path

def get_daily_shayri_topic():
    print("🔍 Fetching a FRESH Shayri Theme from AI...")
    prompt = f"Give me ONLY ONE unique and deep Hindi Shayri theme or emotion (like unspoken love, deep motivation, betrayal, beautiful life, rain nostalgia, moving on) for {CURRENT_YEAR}. Keep it under 4 words. No quotes."
    safe_prompt = urllib.parse.quote(prompt)
    
    max_retries = 5
    for _ in range(max_retries):
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=15)
            fresh_topic = res.text.strip().replace('"', '').replace("'", "")
            if 3 < len(fresh_topic) < 40:
                return fresh_topic
        except Exception:
            time.sleep(2)
            
    return f"Deep feelings of {datetime.datetime.now().strftime('%A')}"

# 🎵 NEW UPGRADE: 100% Dynamic Online BGM Downloader (No Hardcoded Local Folder)
def download_dynamic_bgm(theme):
    print(f"🎵 Analyzing theme '{theme}' to fetch matching Copyright-Free BGM online...")
    
    # AI se mood and genre pucha ja raha hai theme ke according
    prompt = f"Based on the poetry theme '{theme}', suggest the single best background music mood keyword from these options: [sad, romantic, motivational, peaceful]. Output ONLY the lowercase keyword, nothing else."
    safe_prompt = urllib.parse.quote(prompt)
    
    mood = "sad" # Default dynamic fallback
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=15)
        detected_mood = res.text.strip().lower()
        if detected_mood in ["sad", "romantic", "motivational", "peaceful"]:
            mood = detected_mood
    except:
        pass

    print(f"🎼 Selected Music Mood: {mood.upper()}")
    
    # High-quality Creative Commons Direct MP3 Links from trusted open archives (Kevin MacLeod / Incompetech & FreeMusicArchive)
    # Yeh internet se direct stream/download honge, local folder ki koi need nahi hai.
    music_sources = {
        "sad": [
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", # Dynamic stream fallbacks
            "https://ccmixter.org/content/Uncontained/Uncontained_-_The_Art_Of_Silence_1.mp3"
        ],
        "romantic": [
            "https://ccmixter.org/content/cdk/cdk_-_Like_Me_Dislike_Me.mp3",
            "https://ccmixter.org/content/airtone/airtone_-_revisions.mp3"
        ],
        "motivational": [
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
            "https://ccmixter.org/content/scotttobias/scotttobias_-_Trance_State.mp3"
        ],
        "peaceful": [
            "https://ccmixter.org/content/airtone/airtone_-_nightWalk.mp3",
            "https://ccmixter.org/content/airtone/airtone_-_allway.mp3"
        ]
    }
    
    selected_url = random.choice(music_sources[mood])
    bgm_filename = "temp_online_bgm.mp3"
    
    try:
        print(f"📥 Downloading copyright-free track dynamically...")
        res = requests.get(selected_url, headers=get_fake_headers(), timeout=30)
        with open(bgm_filename, 'wb') as f:
            f.write(res.content)
        return bgm_filename
    except Exception as e:
        print(f"⚠️ Music download failed: {e}. Running video without BGM to ensure no crash.")
        return None

def clean_ai_text(text):
    text = re.sub(r'(?i)(Shayri|Voiceover|Scene|Label|:|-)', '', text)
    return text.strip()

def apply_random_motion(clip, duration):
    clip = clip.resize(width=1242, height=2208)
    effects = ['pan_left', 'pan_right', 'pan_up', 'pan_down', 'zoom_in']
    effect = random.choice(effects)
    
    if effect == 'pan_left': return clip.set_position(lambda t: (-162 * (t/duration), 'center'))
    elif effect == 'pan_right': return clip.set_position(lambda t: (-162 + (162 * (t/duration)), 'center'))
    elif effect == 'pan_up': return clip.set_position(lambda t: ('center', -288 * (t/duration)))
    elif effect == 'zoom_in': return clip.resize(lambda t: 1 + 0.1 * (t/duration)).set_position('center')
    else: return clip.set_position(lambda t: ('center', -288 + (288 * (t/duration))))

def generate_youtube_metadata(topic):
    print("📝 Generating SEO Title, Description & Tags for @mistahub...")
    prompt = f"Write highly engaging YouTube Shorts metadata for a Hindi Shayri about: '{topic}'. Mention @mistahub in description. Format exactly like this:\nTITLE: Catchy Title #shorts\nDESCRIPTION: Short description.\nTAGS: tag1, tag2"
    safe_prompt = urllib.parse.quote(prompt)
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=20)
        text = res.text
        title = text.split("TITLE:")[1].split("DESCRIPTION:")[0].strip() if "TITLE:" in text else f"Heart touching Shayri on {topic} 💔 #shayri #shorts"
        desc = text.split("DESCRIPTION:")[1].split("TAGS:")[0].strip() if "DESCRIPTION:" in text else f"Deep words about {topic}. Subscribe to @mistahub for daily soul-touching poetry."
        tags_str = text.split("TAGS:")[1].strip() if "TAGS:" in text else "shayri, shorts, hindi, poetry, mistahub, status"
        tags = [t.strip() for t in tags_str.split(',')][:15]
        
        for t in ["shayri", "shorts", "mistahub"]:
            if t not in [tag.lower() for tag in tags]: tags.append(t)
            
        return title, desc, tags[:15]
    except:
        date_str = datetime.datetime.now().strftime("%d %b")
        return f"Beautiful Shayri on {topic} ✨ | @mistahub #shorts", f"Daily Shayri Drop ({date_str}). Follow @mistahub for more emotional poetry.", ["shayri", "shorts", "mistahub", "poetry", "hindi"]

def upload_video_to_youtube(video_path, title, description, tags):
    print("\n🚀 Uploading @mistahub Shayri to YouTube...")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! (Set as GitHub Secrets for fully auto manager mode)")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "24",
            "defaultLanguage": "hi"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    try:
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
        response = req.execute()
        print(f"🎉 SHAYRI UPLOADED SUCCESSFULLY! Link: https://youtube.com/shorts/{response['id']}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

def process_scene_data(index, hindi_text, img_prompt, unique_seed):
    print(f"   ⚡ Generating Shayri Scene {index+1}...")
    audio_file = f"temp_audio_{index}.mp3"
    
    clean_speech = clean_ai_text(hindi_text)
    asyncio.run(generate_audio(clean_speech, audio_file))
    
    safe_img = urllib.parse.quote(f"{img_prompt.strip()}, highly detailed, cinematic lighting, moody, 9:16 aspect ratio, 4k resolution")
    img_url = f"https://image.pollinations.ai/prompt/{safe_img}?width=1080&height=1920&nologo=true&seed={unique_seed+index}"
    img_file = f"temp_scene_{index}.jpg"
    
    image_success = False
    for _ in range(3):
        try:
            res = requests.get(img_url, headers=get_fake_headers(), timeout=30)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(img_file, 'wb') as f: f.write(res.content)
                image_success = True
                break
        except: time.sleep(2)
            
    if not image_success:
        Image.new('RGB', (1080, 1920), color=(15,15,15)).save(img_file)
            
    return index, audio_file, img_file, clean_speech

def cleanup_temp_files():
    print("🧹 Cleaning up temporary files...")
    for file in glob.glob("temp_*.*"):
        try: os.remove(file)
        except: pass

def main():
    trending_topic = get_daily_shayri_topic()
    unique_seed = random.randint(10000, 999999)
    font_path = download_hindi_font()
    
    print(f"🚀 Shayri Theme Selected: {trending_topic}")
    
    text_prompt = f"You are a master Hindi Shayar. Write a deep, emotional, and beautiful Hindi Shayri about: '{trending_topic}'. Write exactly 4 lines. Output ONLY the raw Hindi Shayri dialogue and an English background image prompt for each line, separated by '|'. Format EXACTLY: [Hindi Shayri Line] | [English Image Prompt]."
    safe_prompt = urllib.parse.quote(text_prompt)
    
    script_lines = []
    print("⏳ AI Shayri likh raha hai...")
    for _ in range(5):
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=45)
            raw_text = res.text.strip()
            script_lines = [line.split('|', 1) for line in raw_text.split('\n') if '|' in line]
            if len(script_lines) >= 3: break
        except: time.sleep(3)
            
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_scene_data, i, text.strip(), img.strip(), unique_seed) for i, (text, img) in enumerate(script_lines)]
        for future in futures: results.append(future.result())

    results.sort(key=lambda x: x[0])
    video_clips = []
    
    for i, audio_file, img_file, hindi_text in results:
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration + 0.3
        
        img_clip = ImageClip(img_file)
        animated_clip = apply_random_motion(img_clip, scene_dur).set_duration(scene_dur)
        
        txt_clip = TextClip(hindi_text, font=font_path, fontsize=70, color='white', method='caption', size=(900, None), align='center')
        txt_bg = ImageClip(Image.new('RGBA', (1000, txt_clip.h + 60), (0, 0, 0, 160))).set_duration(scene_dur).set_position('center')
        txt_clip = txt_clip.set_duration(scene_dur).set_position('center')
        
        watermark = TextClip("@mistahub", font=font_path, fontsize=45, color='rgba(255,255,255,0.7)').set_duration(scene_dur).set_position(('center', 1650))
        
        dark_overlay = ImageClip(Image.new('RGB', (1080, 1920), color=(0,0,0))).set_opacity(0.3).set_duration(scene_dur)
        
        synced_clip = CompositeVideoClip([animated_clip.set_position('center'), dark_overlay, txt_bg, txt_clip, watermark], size=(1080, 1920)).set_audio(audio_clip)
        
        if i > 0: synced_clip = synced_clip.crossfadein(0.5)
        video_clips.append(synced_clip)

    final_video = concatenate_videoclips(video_clips, method="compose", padding=-0.5)
    
    # 🎵 100% AUTOMATED BGM MIXING FROM WEB (No hardcoded folder)
    bgm_file = download_dynamic_bgm(trending_topic)
    if bgm_file and os.path.exists(bgm_file):
        try:
            print(f"🎵 Mixing Dynamic Online BGM...")
            bgm_clip = AudioFileClip(bgm_file).fx(lambda x: x.volumex(0.12)).set_duration(final_video.duration)
            final_audio = CompositeAudioClip([final_video.audio, bgm_clip])
            final_video = final_video.set_audio(final_audio)
        except Exception as e:
            print(f"⚠️ Error mixing BGM: {e}")

    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_video_name = f"mistahub_ULTRA_{date_str}.mp4"

    print("\n⚡ Rendering Ultra Agent Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    title, desc, tags = generate_youtube_metadata(trending_topic)
    upload_video_to_youtube(final_video_name, title, desc, tags)
    
    cleanup_temp_files()

if __name__ == "__main__":
    main()
