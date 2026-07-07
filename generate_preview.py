import os
import requests
import asyncio
import sys
import urllib.parse
import random
import time
import re
import edge_tts
from concurrent.futures import ThreadPoolExecutor
from pytrends.request import TrendReq
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip, TextClip
from PIL import Image

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_fake_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]
    fake_ip = f"{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}.{random.randint(11,250)}"
    return {"User-Agent": random.choice(user_agents), "X-Forwarded-For": fake_ip, "Client-IP": fake_ip}

async def generate_audio(text, filename):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+12%")
    await communicate.save(filename)

def download_hindi_font():
    font_path = "HindiFont.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/noto-fonts/raw/main/unhinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        res = requests.get(url, headers=get_fake_headers())
        with open(font_path, 'wb') as f: f.write(res.content)
    return font_path

# 🔴 NICHE-SPECIFIC TREND ENGINE
def get_daily_trending_topic():
    print("🔍 Scanning Your Niche (SEO, Dev, Earning, Tools)...")
    # Yeh aapke channel ke core keywords hain
    niches = ["YouTube SEO", "Earn money online", "Free AI tools", "Android App Development", "Website development", "Channel growth secrets"]
    seed = random.choice(niches)
    
    try:
        pytrend = TrendReq(hl='en-IN', tz=330, timeout=(10,25), retries=3, requests_args={'headers': get_fake_headers()})
        pytrend.build_payload(kw_list=[seed], geo='IN', timeframe='today 1-m')
        rising = pytrend.related_queries()[seed]['rising']
        
        # Agar India me log kuch specific search kar rahe hain is keyword par, toh wo uthayega
        if rising is not None and not rising.empty:
            trending_query = random.choice(rising['query'].tolist()).title()
            return f"{trending_query} ({seed})"
    except Exception as e:
        print(f"⚠️ Trend fetch failed: {e}")
    
    return f"Secret {seed} Hacks 2026"

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
    print("📝 Generating SEO Title, Description & Tags...")
    prompt = f"Write highly engaging YouTube Shorts metadata for a tech/education channel about: '{topic}'. Format exactly like this:\nTITLE: Catchy Title #shorts\nDESCRIPTION: Short description.\nTAGS: tag1, tag2, tag3"
    safe_prompt = urllib.parse.quote(prompt)
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}", headers=get_fake_headers(), timeout=30)
        text = res.text
        title = text.split("TITLE:")[1].split("DESCRIPTION:")[0].strip() if "TITLE:" in text else f"{topic} Hacks #shorts"
        desc = text.split("DESCRIPTION:")[1].split("TAGS:")[0].strip() if "DESCRIPTION:" in text else "Subscribe for more Tech & Growth hacks!"
        tags_str = text.split("TAGS:")[1].strip() if "TAGS:" in text else "shorts, tech, seo, earning"
        tags = [t.strip() for t in tags_str.split(',')][:15]
        
        # Ensure niche-specific tags are always included
        if "seo" not in tags_str.lower(): tags.append("seo")
        if "grow" not in tags_str.lower(): tags.append("youtube growth")
        
        return title, desc, tags[:15]
    except:
        return f"Secret Tech Hacks #shorts", "Watch this trending video! Subscribe.", ["shorts", "tech", "seo", "appdev", "earning"]

def upload_video_to_youtube(video_path, title, description, tags):
    print("\n🚀 Uploading Video to YouTube with Niche SEO Settings...")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ YouTube Credentials missing! Skipping upload.")
        return

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27", # Education
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
    
    # Updated image prompt for a more "tech/digital" aesthetic
    safe_img = urllib.parse.quote(f"{img_prompt.strip()}, tech startup vibe, coding screen, digital art, ultra realistic, 9:16 aspect ratio, cinematic")
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
        Image.new('RGB', (1080, 1920), color=(15, 20, 30)).save(img_file)
            
    return index, audio_file, img_file, clean_speech, image_success

def main():
    trending_topic = get_daily_trending_topic()
    unique_seed = random.randint(1, 999999)
    font_path = download_hindi_font()
    
    print(f"🚀 Concept Selected: {trending_topic}")
    
    text_prompt = f"You are a Tech/SEO expert YouTuber. Write a viral Hindi YouTube Shorts script teaching about: '{trending_topic}'. Give practical tips. The 6th scene MUST ask to Subscribe. Output ONLY the raw Hindi dialogue and the Image prompt separated by '|'. NO labels like 'Voiceover:', NO prefixes. Format EXACTLY 6 lines: [Raw Hindi Text] | [English Image Prompt]. Unique ID: {unique_seed}"
    safe_prompt = urllib.parse.quote(text_prompt)
    
    raw_text = ""
    try:
        res = requests.get(f"https://text.pollinations.ai/prompt/{safe_prompt}", headers=get_fake_headers(), timeout=45)
        raw_text = res.text.strip()
    except: pass
    
    script_lines = [line.split('|', 1) for line in raw_text.split('\n') if '|' in line]
    if len(script_lines) < 3: 
        print("⚠️ AI generation failed. Using niche fallback.")
        fallback = f"""क्या आप भी {trending_topic} मास्टर करना चाहते हैं? | A cinematic shot of a laptop screen with glowing code and graphs, 4k.
आजकल बिना सही स्ट्रेटेजी के ऑनलाइन ग्रो करना नामुमकिन है। | A frustrated person looking at zero views on screen, dark room.
सबसे पहले, आपको सही कीवर्ड्स और टूल्स का इस्तेमाल करना होगा। | A glowing search bar with digital data flowing out of it.
साथ ही, अपनी ऑडियंस को हुक करने के लिए सस्पेंस बनाना सीखें। | A glowing brain inside a lightbulb, digital art.
यही वो सीक्रेट है जो बड़े क्रिएटर्स आपसे छुपाते हैं। | A sleek modern workspace with dual monitors, glowing keyboard.
अगर ऐसी ही प्रीमियम टिप्स फ्री में चाहिए, तो अभी सब्सक्राइब करें! | A glowing neon subscribe button hovering over a smartphone."""
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
    final_video_name = "latest_educational_video.mp4"

    print("\n⚡ Rendering Video...")
    final_video.write_videofile(final_video_name, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2, logger=None)

    title, desc, tags = generate_youtube_metadata(trending_topic)
    upload_video_to_youtube(final_video_name, title, desc, tags)

if __name__ == "__main__":
    main()
