import requests, os, random, json
from moviepy.editor import ImageClip, TextClip, AudioFileClip, CompositeVideoClip

# Secrets
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
FREESOUND_KEY = os.getenv('FREESOUND_API_KEY')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def get_quote():
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = "Write a short 1-sentence motivational quote by Lucas Hart. Also give a title and 8 hashtags."
    res = requests.post(url, headers={"Authorization": f"Bearer {OPENROUTER_KEY}"}, 
                        json={"model": "google/gemini-2.0-flash-exp:free", "messages": [{"role": "user", "content": prompt}]})
    return res.json()['choices'][0]['message']['content']

def get_image():
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=nature+greenery&orientation=vertical&per_page=20"
    hits = requests.get(url).json()['hits']
    img_url = random.choice(hits)['largeImageURL']
    with open('bg.jpg', 'wb') as f: f.write(requests.get(img_url).content)
    return 'bg.jpg'

def get_music():
    # Freesound se soft piano music search karna
    search_url = f"https://freesound.org/apiv2/search/text/?query=piano+soft+deep&token={FREESOUND_KEY}&filter=duration:[10+TO+60]"
    sound_id = requests.get(search_url).json()['results'][0]['id']
    download_url = f"https://freesound.org/apiv2/sounds/{sound_id}/?token={FREESOUND_KEY}"
    file_url = requests.get(download_url).json()['previews']['preview-hq-mp3']
    with open('music.mp3', 'wb') as f: f.write(requests.get(file_url).content)
    return 'music.mp3'

def create_video(quote):
    # Image clip 8 seconds ki
    clip = ImageClip(get_image()).set_duration(8)
    
    # Text overlay (Quote + Author)
    txt = TextClip(f"{quote}\n\n- Lucas Hart", fontsize=50, color='white', font='Arial-Bold', 
                   method='caption', size=(720, 1280)).set_duration(8).set_position('center')
    
    # Audio add karna
    audio = AudioFileClip(get_music()).subclip(0, 8)
    
    video = CompositeVideoClip([clip, txt]).set_audio(audio)
    video.write_videofile("short.mp4", fps=24, codec="libx264")
    return "short.mp4"

def upload_catbox(file):
    with open(file, 'rb') as f:
        res = requests.post("https://catbox.moe/user/api.php", 
                            data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
    return res.text

# Run
content = get_quote()
video_file = create_video(content)
catbox_url = upload_catbox(video_file)

# Post to TG & Webhook
requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo", data={"chat_id": TG_CHAT_ID, "video": catbox_url, "caption": content})
requests.post(WEBHOOK_URL, json={"video_url": catbox_url, "caption": content})
