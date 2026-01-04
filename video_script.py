import requests, os, random, json
from moviepy.editor import ImageClip, TextClip, AudioFileClip, CompositeVideoClip

# API Keys from GitHub Secrets
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
FREESOUND_KEY = os.getenv('FREESOUND_API_KEY')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

AUTHOR = "Lucas Hart"
DURATION = 5  # Duration set to 5 seconds

def get_ai_data():
    """Sirf quote aur title lena (Strict 50 char limit)"""
    prompt = f"Provide a unique motivational quote by {AUTHOR} (max 45 chars). No stars, no labels. Just the sentence."
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    # Cleaning AI response
    raw_quote = res.json()['choices'][0]['message']['content'].strip()
    clean_quote = raw_quote.replace("*", "").replace('"', "").replace("Quote:", "").strip()
    return clean_quote[:50] # Hard limit 50 chars

def get_unique_img():
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=nature+forest+landscape&orientation=vertical&per_page=100"
    hits = requests.get(url).json()['hits']
    
    if os.path.exists("video_history.txt"):
        with open("video_history.txt", "r") as f:
            history = f.read().splitlines()
    else: history = []

    for hit in hits:
        if str(hit['id']) not in history:
            with open("video_history.txt", "a") as f: f.write(str(hit['id']) + "\n")
            with open('bg.jpg', 'wb') as f: f.write(requests.get(hit['largeImageURL']).content)
            return 'bg.jpg'
    return None

def create_video(quote):
    # Background Image
    clip = ImageClip(get_unique_img()).set_duration(DURATION)
    
    # HIGHLIGHT LOGIC: Quote ko highlight karne ke liye semi-transparent background
    # Font size 75 for better visibility
    txt_clip = TextClip(
        f"{quote}\n\n- {AUTHOR}",
        fontsize=75, 
        color='white', 
        font='Arial-Bold',
        method='caption',
        size=(900, None), # Width adjusted for highlight
        bg_color='black', # Black background highlight
        stroke_color='white',
        stroke_width=1
    ).set_duration(DURATION).set_opacity(0.85).set_position('center')
    
    # Background Music
    search = f"https://freesound.org/apiv2/search/text/?query=piano+ambient&token={FREESOUND_KEY}"
    sound_id = requests.get(search).json()['results'][0]['id']
    sound_info = requests.get(f"https://freesound.org/apiv2/sounds/{sound_id}/?token={FREESOUND_KEY}").json()
    with open('music.mp3', 'wb') as f: f.write(requests.get(sound_info['previews']['preview-hq-mp3']).content)
    
    audio = AudioFileClip('music.mp3').subclip(0, DURATION)
    
    # Merge and Export
    video = CompositeVideoClip([clip, txt_clip]).set_audio(audio)
    video.write_videofile("final_video.mp4", fps=24, codec="libx264")
    return "final_video.mp4"

def upload_to_catbox(file):
    with open(file, 'rb') as f:
        res = requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
    return res.text.strip()

# Execution Sequence
try:
    final_quote = get_ai_data()
    video_file = create_video(final_quote)
    catbox_url = upload_to_catbox(video_file)

    # 8 Hashtags fix
    hashtags = "#motivation #quotes #lucashart #nature #shorts #success #mindset #viral"
    caption = f"{final_quote}\n\n{hashtags}"

    # Send to Telegram
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo", 
                  data={"chat_id": TG_CHAT_ID, "video": catbox_url, "caption": caption})
    
    # Send to Webhook
    requests.post(WEBHOOK_URL, json={"url": catbox_url, "quote": final_quote, "hashtags": hashtags})
    
    print(f"Success! URL: {catbox_url}")
except Exception as e:
    print(f"Error: {e}")
