import os
import requests
import asyncio
import urllib.parse
import random
import time
import re
import edge_tts
import datetime
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
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
    # MadhurNeural ko thoda slow kiya hai shayri feel ke liye
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-5%")
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
    prompt = f"Give me ONLY ONE unique and deep Hindi Shayri theme or emotion (like unspoken love, deep motivation, betrayal, beautiful life, rain nostalgia) for {CURRENT_YEAR}. Keep it under 4 words. No quotes."
    safe_prompt = urllib.parse.quote(prompt)
    
    # Koi hardcoded fallback list nahi hai, AI fail hua toh loop chalega
    max_retries = 5
    for _ in range(max_retries):
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=15)
            fresh_topic = res.text.strip().replace('"', '').replace("'", "")
            if 3 < len(fresh_topic) < 40:
                return fresh_topic
        except Exception:
            time.sleep(2)
            
    # Agar 5 baar try karne pe bhi AI na chale, toh aaj ka din ka naam dynamic fallback hoga
    return f"Deep feelings of {datetime.datetime.now().strftime('%A')}"

def clean_ai_text(text):
    text = re.sub(r'(?i)(Shayri|Voiceover|Scene|Label|:|-)', '', text)
    return text.strip()

def apply_random_motion(clip, duration):
    clip = clip.resize(width=1242, height=2208)
    effects = ['pan_left', 'pan_right', 'pan_up', 'pan_down']
    effect = random.choice(effects)
    
    if effect == 'pan_left': return clip.set_position(lambda t: (-162 * (t/duration), 'center'))
    elif effect == 'pan_right': return clip.set_position(lambda t: (-162 + (162 * (t/duration)), 'center'))
    elif effect == 'pan_up': return clip.set_position(lambda t: ('center', -288 * (t/duration)))
    else: return clip.set_position(lambda t: ('center', -288 + (288 * (t/duration))))

def generate_youtube_metadata(topic):
    print("📝 Generating SEO Title, Description & Tags for @mistahub...")
    prompt = f"Write highly engaging YouTube Shorts metadata for a Hindi Shayri about: '{topic}'. Mention @mistahub in description. Format exactly like this:\nTITLE: Catchy Title #shayri #shorts\nDESCRIPTION: Short description.\nTAGS: tag1, tag2"
    safe_prompt = urllib.parse.quote(prompt)
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=20)
        text = res.text
        title = text.split("TITLE:")[1].split("DESCRIPTION:")[0].strip() if "TITLE:" in text else f"Heart touching Shayri on {topic} 💔 #shayri #shorts"
        desc = text.split("DESCRIPTION:")[1].split("TAGS:")[0].strip() if "DESCRIPTION:" in text else f"Deep words about {topic}. Subscribe to @mistahub for daily soul-touching poetry."
        tags_str = text.split("TAGS:")[1].strip() if "TAGS:" in text else "shayri, shorts, hindi, poetry, mistahub, status"
        tags = [t.strip() for t in tags_str.split(',')][:15]
        
        # Tags me mandatory '@mistahub' and 'shayri' ensure kar rahe hai
        for t in ["shayri", "shorts", "mistahub"]:
            if t not in [tag.lower() for tag in tags]: tags.append(t)
            
        return title, desc, tags[:15]
    except:
        # Dynamic datetime based metadata if AI fails
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
            "categoryId": "24", # Category changed to Entertainment/Shayri
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

def create_shayri_text(text, duration, font_path):
    # Text hamesha show hoga kyuki shayri readable honi chahiye
    txt = TextClip(text, font=font_path, fontsize=65, color='white', stroke_color='black', stroke_width=3, method='caption', size=(900, None), align='center')
    return txt.set_duration(duration).set_position('center')

def process_scene_data(index, hindi_text, img_prompt, unique_seed):
    print(f"   ⚡ Generating Shayri Scene {index+1}...")
    audio_file = f"audio_{index}.mp3"
    
    clean_speech = clean_ai_text(hindi_text)
    asyncio.run(generate_audio(clean_speech, audio_file))
    
    # Emotional aur cinematic backgrounds
    safe_img = urllib.parse.quote(f"{img_prompt.strip()}, highly detailed, beautiful lighting, emotional, 9:16 aspect ratio, 4k wallpaper")
    img_url = f"https://image.pollinations.ai/prompt/{safe_img}?width=1080&height=1920&nologo=true&seed={unique_seed+index}"
    img_file = f"scene_{index}.jpg"
    
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
        Image.new('RGB', (1080, 1920), color=(random.randint(5,20), random.randint(5,20), random.randint(5,20))).save(img_file)
            
    return index, audio_file, img_file, clean_speech

def main():
    trending_topic = get_daily_shayri_topic()
    unique_seed = random.randint(10000, 999999)
    font_path = download_hindi_font()
    
    print(f"🚀 Shayri Theme Selected: {trending_topic}")
    
    # AI Prompt specially crafted for Shayri Generation
    text_prompt = f"You are a master Hindi Shayar. Write a deep, emotional, and beautiful Hindi Shayri about: '{trending_topic}'. Write 4 to 6 lines. Output ONLY the raw Hindi Shayri dialogue and an English background image prompt for each line, separated by '|'. Format EXACTLY: [Hindi Shayri Line] | [English Image Prompt]."
    safe_prompt = urllib.parse.quote(text_prompt)
    
    script_lines = []
    # No Hardcoded Array! Yeh while loop tab tak chalega jab tak AI sahi script na de de. (Agent logic)
    print("⏳ AI Shayri likh raha hai...")
    while len(script_lines) < 3:
        try:
            res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=45)
            raw_text = res.text.strip()
            script_lines = [line.split('|', 1) for line in raw_text.split('\n') if '|' in line]
        except:
            time.sleep(3)
            
    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_scene_data, i, text.strip(), img.strip(), unique_seed) for i, (text, img) in enumerate(script_lines)]
        for future in futures: results.append(future.result())

    results.sort(key=lambda x: x[0])
    video_clips = []
    
    for i, audio_file, img_file, hindi_text in results:
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration
        
        img_clip = ImageClip(img_file)
        animated_clip = apply_random_motion(img_clip, scene_dur).set_duration(scene_dur)
        
        # Shayri video ke liye text zaroori hai, isiliye isko mandatory add kiya gaya
        txt_clip = create_shayri_text(hindi_text, scene_dur, font_path)
        
        # Text clear dikhe iske liye peeche ek dark overlay lagaya
        dark_overlay = ImageClip(Image.new('RGB', (1080, 1920), color=(0,0,0))).set_opacity(0.4).set_duration(scene_dur)
        
        synced_clip = CompositeVideoClip([animated_clip.set_position('center'), dark_overlay, txt_clip], size=(1080, 1920)).set_audio(audio_clip)
        
        if i > 0: synced_clip = synced_clip.crossfadein(0.5)
        video_clips.append(synced_clip)

    final_video = concatenate_videoclips(video_clips, method="compose", padding=-0.5)
    
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_video_name = f"mistahub_shayri_{date_str}.mp4"

    print("\n⚡ Rendering Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    title, desc, tags = generate_youtube_metadata(trending_topic)
    upload_video_to_youtube(final_video_name, title, desc, tags)

if __name__ == "__main__":
    main()
