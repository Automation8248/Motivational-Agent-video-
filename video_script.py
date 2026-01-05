import requests, os, random, json, time

# PIL Fix for moviepy compatibility
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, TextClip, AudioFileClip, CompositeVideoClip

# Config & Keys
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
FREESOUND_KEY = os.getenv('FREESOUND_API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

DURATION = 5

def get_free_quote():
    """ZenQuotes API se free motivational quotes pick karega"""
    try:
        # Free API - No Key Required
        res = requests.get("https://zenquotes.io/api/random", timeout=15)
        data = res.json()[0]
        quote = data['q']
        author = data['a']
        return quote, author
    except Exception as e:
        print(f"Quote Fetch Error: {e}")
        return "Your only limit is your mind.", "Anonymous"

def get_real_nature_img():
    """Pixabay se clean nature photo pick karega (No CGI/Animation)"""
    query = "nature+landscape+forest+mountain+-cgi+-animation+-vector"
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=vertical&per_page=50"
    
    try:
        response = requests.get(url, timeout=15).json()
        hits = response.get('hits', [])
        
        # Repetition rokne ke liye history check
        history_file = "video_history.txt"
        history = open(history_file, "r").read().splitlines() if os.path.exists(history_file) else []
        
        random.shuffle(hits)
        for hit in hits:
            if str(hit['id']) not in history:
                img_data = requests.get(hit['largeImageURL'], timeout=15).content
                if img_data:
                    with open('bg.jpg', 'wb') as f: f.write(img_data)
                    with open(history_file, "a") as f: f.write(str(hit['id']) + "\n")
                    return 'bg.jpg'
    except: return None

def create_video(quote, author):
    """Video banayega: Pure White Text + Dark Nature Background"""
    bg_path = get_real_nature_img()
    if not bg_path: raise Exception("Image download fail ho gayi.")

    # 1. Background (Darkened for white text visibility)
    bg = ImageClip(bg_path).set_duration(DURATION).resize(height=1920).fl_image(lambda image: (image * 0.6).astype('uint8'))
    
    # 2. Text (Pure White, No Stroke)
    full_text = f"\"{quote}\"\n\n- {author}"
    txt = TextClip(full_text, fontsize=65, color='white', font='Arial-Bold', 
                   method='caption', size=(850, None), stroke_width=0).set_duration(DURATION).set_position('center')
    
    # 3. Audio (Piano Music)
    try:
        search = f"https://freesound.org/apiv2/search/text/?query=piano+soft&token={FREESOUND_KEY}"
        s_id = requests.get(search, timeout=10).json()['results'][0]['id']
        info = requests.get(f"https://freesound.org/apiv2/sounds/{s_id}/?token={FREESOUND_KEY}", timeout=10).json()
        audio_url = info['previews']['preview-hq-mp3']
        with open('music.mp3', 'wb') as f: f.write(requests.get(audio_url).content)
        audio = AudioFileClip('music.mp3').subclip(0, DURATION)
    except: audio = None
    
    final = CompositeVideoClip([bg, txt])
    if audio: final = final.set_audio(audio)
    
    final.write_videofile("final_short.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final_short.mp4"

# --- Main Flow ---
try:
    print("Step 1: Fetching Free Quote...")
    quote_text, author_name = get_free_quote()
    
    print("Step 2: Creating Video...")
    video_file = create_video(quote_text, author_name)
    
    print("Step 3: Uploading to Catbox...")
    with open(video_file, 'rb') as f:
        catbox_url = requests.post("https://catbox.moe/user/api.php", 
                                    data={'reqtype': 'fileupload'}, files={'fileToUpload': f}).text.strip()
    
    if "http" in catbox_url:
        # Title and Caption for Social Media
        title = f"Daily Inspiration: {author_name}"
        caption = f"🎬 **{title}**\n\n✨ {quote_text}\n\n#motivation #nature #quotes #shorts #success #mindset"
        
        print("Step 4: Sending to Telegram & Webhook...")
        # Telegram Post
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo", 
                      data={"chat_id": TG_CHAT_ID, "video": catbox_url, "caption": caption, "parse_mode": "Markdown"})
        
        # Webhook for Make.com (URL Mapping Fixed)
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"url": catbox_url, "title": title, "caption": caption}, timeout=10)
        
        print(f"Workflow Complete! Link: {catbox_url}")
    else:
        print("Catbox Upload Failed.")

except Exception as e:
    print(f"Fatal Error: {e}")
