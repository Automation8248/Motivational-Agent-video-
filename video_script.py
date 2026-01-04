import requests, os, random, json
from moviepy.editor import ImageClip, TextClip, AudioFileClip, CompositeVideoClip, ColorClip

# API Keys
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
FREESOUND_KEY = os.getenv('FREESOUND_API_KEY')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

AUTHOR = "Lucas Hart"
DURATION = 5 

def get_ai_data():
    """AI se quote aur short title/caption mangwana"""
    prompt = f"Write 1 unique short motivational quote by {AUTHOR}. Max 45 characters. Also give a 5-word title and 8 hashtags. No stars, no labels."
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    raw_text = res.json()['choices'][0]['message']['content'].strip()
    # Cleaning
    clean_text = raw_text.replace("*", "").replace('"', "").replace("Quote:", "").replace("Title:", "").strip()
    return clean_text

def get_img():
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=nature+forest+mountain&orientation=vertical&per_page=100"
    hits = requests.get(url).json()['hits']
    
    if os.path.exists("video_history.txt"):
        with open("video_history.txt", "r") as f: history = f.read().splitlines()
    else: history = []

    for hit in hits:
        if str(hit['id']) not in history:
            with open("video_history.txt", "a") as f: f.write(str(hit['id']) + "\n")
            with open('bg.jpg', 'wb') as f: f.write(requests.get(hit['largeImageURL']).content)
            return 'bg.jpg'
    return None

def create_video(quote):
    # Background Image
    bg = ImageClip(get_img()).set_duration(DURATION).resize(height=1920) # Shorts Size
    
    # Highlight Box (Text ke piche halka black parda taaki quote highlight ho)
    shadow = ColorClip(size=(900, 450), color=(0,0,0)).set_opacity(0.4).set_duration(DURATION).set_position('center')

    # Quote Text (Bada size aur Center)
    txt = TextClip(f"{quote}\n\n- {AUTHOR}", fontsize=75, color='white', font='Arial-Bold',
                   method='caption', size=(850, None), align='Center').set_duration(DURATION).set_position('center')
    
    # Music
    search = f"https://freesound.org/apiv2/search/text/?query=piano+soft&token={FREESOUND_KEY}"
    sound_id = requests.get(search).json()['results'][0]['id']
    info = requests.get(f"https://freesound.org/apiv2/sounds/{sound_id}/?token={FREESOUND_KEY}").json()
    with open('music.mp3', 'wb') as f: f.write(requests.get(info['previews']['preview-hq-mp3']).content)
    
    audio = AudioFileClip('music.mp3').subclip(0, DURATION)
    
    # Final Merged Video
    final = CompositeVideoClip([bg, shadow, txt]).set_audio(audio)
    final.write_videofile("short.mp4", fps=24, codec="libx264")
    return "short.mp4"

def upload_catbox(file):
    with open(file, 'rb') as f:
        return requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'fileupload'}, files={'fileToUpload': f}).text.strip()

# Final Execution
try:
    content = get_ai_data()
    # Title/Caption control (Max 50 chars)
    short_caption = content.split('\n')[0][:50] 
    hashtags = "#motivation #shorts #lucashart #nature #quotes #success #inspiration #mindset"

    video_file = create_video(content.split('\n')[0]) # Sirf Quote video par dikhega
    catbox_url = upload_catbox(video_file)

    # Telegram & Webhook
    final_msg = f"✨ {short_caption}\n\n{hashtags}"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo", data={"chat_id": TG_CHAT_ID, "video": catbox_url, "caption": final_msg})
    requests.post(WEBHOOK_URL, json={"video_url": catbox_url, "caption": final_msg})

    print(f"Success: {catbox_url}")
except Exception as e:
    print(f"Error: {e}")
