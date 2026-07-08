import os
import requests
import asyncio
import sys
import urllib.parse
import random
import time
import re
import edge_tts
import datetime
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip, TextClip
from PIL import Image

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Aaj ka saal dynamically nikalne ke liye
CURRENT_YEAR = datetime.datetime.now().year

def get_fake_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    ]
    fake_ip = f"{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}"
    return {"User-Agent": random.choice(user_agents), "X-Forwarded-For": fake_ip, "Client-IP": fake_ip}

async def generate_audio(text, filename):
    # MadhurNeural ki jagah SwaraNeural ya koi aur bhi random kar sakte hain future me
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+12%")
    await communicate.save(filename)

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers())
        with open(font_path, 'wb') as f: f.write(res.content)
    return font_path

# 🔴 100% FRESH TOPIC GENERATOR (No Hardcoded Niches)
def get_daily_trending_topic():
    print("🔍 Fetching a completely FRESH & UNIQUE Topic from AI...")
    
    # Hum AI se hi direct ek naya topic maang rahe hain taaki roz din me 3 baar alag topic mile
    prompt = f"Give me ONLY ONE highly engaging, unseen micro-topic name for a YouTube short about Tech, AI, App Development, or Online Earning in {CURRENT_YEAR}. Keep it under 6 words. No quotes, no extra text."
    safe_prompt = urllib.parse.quote(prompt)
    
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=20)
        fresh_topic = res.text.strip().replace('"', '').replace("'", "")
        if 5 < len(fresh_topic) < 60:
            return fresh_topic
    except Exception as e:
        print(f"⚠️ AI Topic fetch failed: {e}")
    
    # Badi dynamic fallback list agar AI fail ho jaye
    fallback_topics = [
        f"Secret AI Tools of {CURRENT_YEAR}",
        "Earn Money with ChatGPT Fast",
        "Hidden Android Developer Tricks",
        "YouTube Shorts Viral Hacks",
        "Zero Investment Online Business",
        "Coding Secrets for Beginners",
        "Best Free AI for Students"
    ]
    return random.choice(fallback_topics)

def clean_ai_text(text):
    text = re.sub(r'(?i)(Spoken Hindi|Voiceover|ID|Scene|Label|:)', '', text)
    return text.strip()

def apply_random_motion(clip, duration):
    clip = clip.resize(width=1242, height=2208)
    effects = ['pan_left', 'pan_right', 'pan_up', 'pan_down']
    effect = random.choice(effects)
    
    if effect == 'pan_left':
        return clip.set_position(lambda t: (-162 * (t/duration), 'center'))
    elif effect == 'pan_right':
        return clip.set_position(lambda t: (-162 + (162 * (t/duration)), 'center'))
    elif effect == 'pan_up':
        return clip.set_position(lambda t: ('center', -288 * (t/duration)))
    else: 
        return clip.set_position(lambda t: ('center', -288 + (288 * (t/duration))))

def generate_youtube_metadata(topic):
    print("📝 Generating Fresh SEO Title, Description & Tags...")
    prompt = f"Write highly engaging YouTube Shorts metadata for: '{topic}'. Format exactly like this:\nTITLE: Catchy Title #shorts\nDESCRIPTION: Short description.\nTAGS: tag1, tag2, tag3"
    safe_prompt = urllib.parse.quote(prompt)
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={random.randint(1,99999)}", headers=get_fake_headers(), timeout=30)
        text = res.text
        title = text.split("TITLE:")[1].split("DESCRIPTION:")[0].strip() if "TITLE:" in text else f"{topic} Craziness #shorts"
        desc = text.split("DESCRIPTION:")[1].split("TAGS:")[0].strip() if "DESCRIPTION:" in text else f"Watch this amazing video about {topic}! Subscribe for more."
        tags_str = text.split("TAGS:")[1].strip() if "TAGS:" in text else "shorts, tech, trending"
        tags = [t.strip() for t in tags_str.split(',')][:15]
        
        if "shorts" not in [t.lower() for t in tags]: tags.append("shorts")
        
        return title, desc, tags[:15]
    except:
        return f"{topic} - Mind Blowing #shorts", f"Learn everything about {topic}. Subscribe!", ["shorts", "tech", "viral", "trending"]

def upload_video_to_youtube(video_path, title, description, tags):
    print("\n🚀 Uploading Video to YouTube...")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Skipping upload. (Check GitHub Secrets)")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27", 
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
        print(f"🎉 VIDEO UPLOADED SUCCESSFULLY! Link: https://youtube.com/shorts/{response['id']}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

def create_typewriter_text(text, duration, font_path):
    words = text.split()
    if not words: return None
    time_per_word = duration / len(words)
    clips = []
    current_text = ""
    for word in words:
        current_text += word + " "
        txt = TextClip(current_text.strip(), font=font_path, fontsize=70, color='yellow', stroke_color='black', stroke_width=4, method='caption', size=(950, None), align='center')
        txt = txt.set_duration(time_per_word)
        clips.append(txt)
    return concatenate_videoclips(clips).set_position('center')

def process_scene_data(index, hindi_text, img_prompt, unique_seed):
    print(f"   ⚡ Generating Scene {index+1}...")
    audio_file = f"audio_{index}.mp3"
    
    clean_speech = clean_ai_text(hindi_text)
    asyncio.run(generate_audio(clean_speech, audio_file))
    
    # Image prompt me bhi seed ka use kiya taaki images hamesha fresh bane
    safe_img = urllib.parse.quote(f"{img_prompt.strip()}, high tech, digital art, highly detailed, 9:16 aspect ratio, cinematic lighting")
    img_url = f"https://image.pollinations.ai/prompt/{safe_img}?width=1080&height=1920&nologo=true&seed={unique_seed+index}"
    img_file = f"scene_{index}.jpg"
    
    image_success = False
    for attempt in range(3):
        try:
            res = requests.get(img_url, headers=get_fake_headers(), timeout=30)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(img_file, 'wb') as f: f.write(res.content)
                image_success = True
                break
        except: time.sleep(2)
            
    if not image_success:
        Image.new('RGB', (1080, 1920), color=(random.randint(10,30), random.randint(10,30), random.randint(20,50))).save(img_file)
            
    return index, audio_file, img_file, clean_speech, image_success

def main():
    trending_topic = get_daily_trending_topic()
    unique_seed = random.randint(10000, 999999)
    font_path = download_hindi_font()
    
    print(f"🚀 Concept Selected: {trending_topic}")
    
    # Promt me seed add kiya taaki har baar alag script aaye
    text_prompt = f"You are a Tech YouTuber. Write a totally unique, viral Hindi YouTube Shorts script about: '{trending_topic}'. Give practical tips. The last scene MUST ask to Subscribe. Output ONLY the raw Hindi dialogue and the English Image prompt separated by '|'. NO labels. Format EXACTLY 6 lines: [Hindi Text] | [English Image Prompt]."
    safe_prompt = urllib.parse.quote(text_prompt)
    
    raw_text = ""
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}?seed={unique_seed}", headers=get_fake_headers(), timeout=45)
        raw_text = res.text.strip()
    except: pass
    
    script_lines = [line.split('|', 1) for line in raw_text.split('\n') if '|' in line]
    
    # Agar AI fail hota hai, tab bhi Fallback hardcoded nahi lagega, wo {trending_topic} ke hisaab se adapt ho jayega
    if len(script_lines) < 3: 
        print("⚠️ AI generation failed. Using dynamic fallback.")
        fallback = f"""क्या आप जानते हैं {trending_topic} के बारे में ये सीक्रेट? | A glowing mystery box with tech symbols, 4k.
ज़्यादातर लोग इस ट्रिक को इग्नोर कर देते हैं, लेकिन ये गेम चेंजर है। | A person looking surprised at a laptop screen.
सबसे पहले, आपको सही स्ट्रेटेजी के साथ काम करना होगा। | A digital roadmap glowing on a desk.
और हाँ, कंसिस्टेंसी ही असली चाबी है। | A glowing key unlocking a digital lock.
यही वो तरीका है जो आपको बाकियों से अलग बनाएगा। | A rocket taking off from a smartphone screen.
ऐसी ही और अमेजिंग टिप्स के लिए अभी चैनल सब्सक्राइब करें! | A glowing neon subscribe button hovering."""
        script_lines = [line.split('|', 1) for line in fallback.split('\n') if '|' in line]

    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_scene_data, i, text.strip(), img.strip(), unique_seed) for i, (text, img) in enumerate(script_lines)]
        for future in futures: results.append(future.result())

    results.sort(key=lambda x: x[0])
    video_clips = []
    
    for i, audio_file, img_file, hindi_text, image_success in results:
        audio_clip = AudioFileClip(audio_file)
        scene_dur = audio_clip.duration
        
        img_clip = ImageClip(img_file)
        animated_clip = apply_random_motion(img_clip, scene_dur).set_duration(scene_dur)
        
        if not image_success:
            txt_clip = create_typewriter_text(hindi_text, scene_dur, font_path)
            video_with_text = CompositeVideoClip([animated_clip.set_position('center'), txt_clip], size=(1080, 1920))
            synced_clip = video_with_text.set_audio(audio_clip)
        else:
            synced_clip = CompositeVideoClip([animated_clip], size=(1080, 1920)).set_audio(audio_clip)
        
        if i > 0: synced_clip = synced_clip.crossfadein(0.4)
        video_clips.append(synced_clip)

    final_video = concatenate_videoclips(video_clips, method="compose", padding=-0.4)
    # File name ko bhi unique banaya gaya hai
    final_video_name = f"shorts_{unique_seed}.mp4"

    print("\n⚡ Rendering Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    title, desc, tags = generate_youtube_metadata(trending_topic)
    upload_video_to_youtube(final_video_name, title, desc, tags)

if __name__ == "__main__":
    main()
