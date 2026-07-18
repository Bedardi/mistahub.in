import os
import requests
import asyncio
import urllib.parse
import random
import time
import re
import datetime
import glob
import textwrap
import edge_tts
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Compatible with MoviePy 1.0.3
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, CompositeAudioClip
import moviepy.audio.fx.all as afx

# YouTube API imports
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
        try:
            res = requests.get(url, headers=get_fake_headers(), timeout=15)
            with open(font_path, 'wb') as f: f.write(res.content)
        except Exception as e:
            print(f"Font download failed: {e}")
    return font_path

def get_daily_shayri_topic():
    print("🔍 Fetching a FRESH Shayri Theme...")
    prompt = f"Give me ONLY ONE unique and deep Hindi Shayri theme or emotion (like unspoken love, deep motivation, betrayal, beautiful life, rain nostalgia, moving on) for {CURRENT_YEAR}. Keep it under 4 words. No quotes."
    safe_prompt = urllib.parse.quote(prompt)
    
    for _ in range(3):
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=10)
            fresh_topic = res.text.strip().replace('"', '').replace("'", "")
            if 3 < len(fresh_topic) < 40: return fresh_topic
        except: time.sleep(2)
            
    return f"Deep feelings of {datetime.datetime.now().strftime('%A')}"

def download_dynamic_bgm():
    print(f"🎵 Fetching dynamic CC BGM...")
    music_sources = [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
    ]
    bgm_filename = "temp_online_bgm.mp3"
    try:
        res = requests.get(random.choice(music_sources), headers=get_fake_headers(), timeout=30)
        with open(bgm_filename, 'wb') as f: f.write(res.content)
        return bgm_filename
    except Exception as e:
        print(f"⚠️ Music download failed: {e}")
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
    print("📝 Generating SEO Metadata...")
    prompt = f"Write highly engaging YouTube Shorts metadata for a Hindi Shayri about: '{topic}'. Mention @mistahub in description. Format exactly like this:\nTITLE: Catchy Title #shorts\nDESCRIPTION: Short description.\nTAGS: tag1, tag2"
    safe_prompt = urllib.parse.quote(prompt)
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=15)
        text = res.text
        title = text.split("TITLE:")[1].split("DESCRIPTION:")[0].strip() if "TITLE:" in text else f"Beautiful Shayri: {topic} ✨ #shayri #shorts"
        desc = text.split("DESCRIPTION:")[1].split("TAGS:")[0].strip() if "DESCRIPTION:" in text else f"Deep words. Subscribe to @mistahub for more."
        tags_str = text.split("TAGS:")[1].strip() if "TAGS:" in text else "shayri, shorts, hindi, poetry, mistahub"
        tags = [t.strip() for t in tags_str.split(',')][:15]
        for t in ["shayri", "shorts", "mistahub"]:
            if t not in [tag.lower() for tag in tags]: tags.append(t)
        return title, desc, tags[:15]
    except:
        return f"Emotional Shayri: {topic} 💔 | @mistahub #shorts", f"Follow @mistahub for daily Hindi poetry.", ["shayri", "shorts", "mistahub", "poetry", "hindi"]

def upload_video_to_youtube(video_path, title, description, tags):
    print("\n🚀 Uploading to YouTube @mistahub...")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Make sure secrets are loaded in GitHub Actions.")
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

# Compatible with Pillow 9.5.0 installed via GitHub Actions
def create_text_overlay(text, font_path, index):
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try: font = ImageFont.truetype(font_path, 65)
    except: font = ImageFont.load_default()
    
    try: wm_font = ImageFont.truetype(font_path, 45)
    except: wm_font = ImageFont.load_default()

    lines = textwrap.wrap(text, width=22)
    total_height = len(lines) * 80
    y_text = (1920 - total_height) // 2

    box_padding = 40
    draw.rectangle([(100, y_text - box_padding), (980, y_text + total_height + box_padding)], fill=(0, 0, 0, 170))

    for line in lines:
        try: 
            # Pillow 9.5.0 compatible text sizing
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
        except: w = len(line) * 30 
        draw.text(((1080 - w) / 2, y_text), line, font=font, fill="white", stroke_width=3, stroke_fill="black")
        y_text += 80

    wm_text = "@mistahub"
    try: 
        bbox = wm_font.getbbox(wm_text)
        w_w = bbox[2] - bbox[0]
    except: w_w = len(wm_text) * 20
    draw.text(((1080 - w_w) / 2, 1650), wm_text, font=wm_font, fill=(255, 255, 255, 200))

    temp_file = f"temp_overlay_{index}.png"
    img.save(temp_file)
    return temp_file

def process_scene_data(index, hindi_text, img_prompt, unique_seed, font_path):
    print(f"   ⚡ Generating Scene {index+1}...")
    audio_file = f"temp_audio_{index}.mp3"
    
    clean_speech = clean_ai_text(hindi_text)
    asyncio.run(generate_audio(clean_speech, audio_file))
    
    safe_img = urllib.parse.quote(f"{img_prompt.strip()}, highly detailed, beautiful lighting, moody, 9:16 aspect ratio, 4k wallpaper")
    img_url = f"https://image.pollinations.ai/prompt/{safe_img}?width=1080&height=1920&nologo=true&seed={unique_seed+index}"
    img_file = f"temp_scene_{index}.jpg"
    
    image_success = False
    for _ in range(3):
        try:
            res = requests.get(img_url, headers=get_fake_headers(), timeout=20)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(img_file, 'wb') as f: f.write(res.content)
                image_success = True
                break
        except: time.sleep(2)
            
    if not image_success:
        Image.new('RGB', (1080, 1920), color=(15,15,15)).save(img_file)
    
    overlay_file = create_text_overlay(clean_speech, font_path, index)
    return index, audio_file, img_file, overlay_file

def cleanup_internal_temp_files():
    # Since GH Actions yaml cleans mp4, mp3, jpg, and ttf, 
    # we just need to clean our specific .png overlays inside the script.
    print("🧹 Cleaning up internal temp PNG overlays...")
    for file in glob.glob("temp_overlay_*.png"):
        try: os.remove(file)
        except: pass

def main():
    trending_topic = get_daily_shayri_topic()
    unique_seed = random.randint(10000, 999999)
    font_path = download_hindi_font()
    
    print(f"🚀 Shayri Theme: {trending_topic}")
    text_prompt = f"You are a master Hindi Shayar. Write a deep, emotional Hindi Shayri about: '{trending_topic}'. Exactly 4 lines. Output EXACTLY format: [Hindi Shayri Line] | [English Image Prompt]."
    safe_prompt = urllib.parse.quote(text_prompt)
    
    script_lines = []
    print("⏳ Generating Script...")
    for _ in range(5):
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=20)
            script_lines = [line.split('|', 1) for line in res.text.strip().split('\n') if '|' in line]
            if len(script_lines) >= 3: break
        except: time.sleep(3)
        
    if len(script_lines) < 3:
        script_lines = [
            ("ज़िंदगी के इस सफर में अजब मोड़ आया", "a lonely road in the dark forest, cinematic"),
            ("मंजिल का पता नहीं, बस चलता चला गया", "footsteps glowing on a rainy street, neon"),
            ("कुछ खवाब टूटे, कुछ अपने छूटे", "broken glass pieces reflecting sad light"),
            ("फिर भी दिल ने कभी हार नहीं माना", "a bright glowing sunrise over dark mountains")
        ]
            
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor: # GH Actions free tier uses 2-core CPU, keeping workers optimal
        futures = [executor.submit(process_scene_data, i, text.strip(), img.strip(), unique_seed, font_path) for i, (text, img) in enumerate(script_lines)]
        for future in futures: results.append(future.result())

    results.sort(key=lambda x: x[0])
    video_clips = []
    
    for i, audio_file, img_file, overlay_file in results:
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration + 0.4
        
        img_clip = ImageClip(img_file)
        animated_clip = apply_random_motion(img_clip, scene_dur).set_duration(scene_dur)
        
        overlay_clip = ImageClip(overlay_file).set_duration(scene_dur).set_position('center')
        dark_overlay = ImageClip(np.array(Image.new('RGB', (1080, 1920), color=(0,0,0)))).set_opacity(0.3).set_duration(scene_dur)
        
        synced_clip = CompositeVideoClip([animated_clip.set_position('center'), dark_overlay, overlay_clip], size=(1080, 1920)).set_audio(audio_clip)
        
        if i > 0: synced_clip = synced_clip.crossfadein(0.5)
        video_clips.append(synced_clip)

    final_video = concatenate_videoclips(video_clips, method="compose", padding=-0.5)
    
    bgm_file = download_dynamic_bgm()
    if bgm_file and os.path.exists(bgm_file):
        try:
            print(f"🎵 Mixing CC BGM...")
            bgm_clip = AudioFileClip(bgm_file).fx(afx.volumex, 0.1)
            bgm_clip = bgm_clip.set_duration(final_video.duration)
            final_audio = CompositeAudioClip([final_video.audio, bgm_clip])
            final_video = final_video.set_audio(final_audio)
        except Exception as e:
            print(f"⚠️ BGM Mix Error (Continuing without BGM): {e}")

    final_video_name = f"mistahub_final_export.mp4"

    print("\n⚡ Rendering Final Video in CI/CD pipeline...")
    # Threads set to 2 to match GitHub Actions runner specs
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    title, desc, tags = generate_youtube_metadata(trending_topic)
    upload_video_to_youtube(final_video_name, title, desc, tags)
    
    cleanup_internal_temp_files()

if __name__ == "__main__":
    main()
