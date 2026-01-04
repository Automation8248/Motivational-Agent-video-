import requests, os, random, json
from moviepy.editor import ImageClip, TextClip, AudioFileClip, CompositeVideoClip

# API Keys
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
FREESOUND_KEY = os.getenv('FREESOUND_API_KEY')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

AUTHOR = "Lucas Hart"
DURATION = 5  # Video duration updated to 5 seconds

def get_ai_quote():
    """Sirf unique quote lene ke liye prompt update kiya gaya hai"""
    prompt = f"Write one short unique motivational quote by {AUTHOR}. Provide ONLY the quote text, no titles, no labels, no stars, no quotes marks. Just the sentence."
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    quote = res.json()['choices'][0]['message']['content'].strip()
    # Cleaning any accidental stars or quotes
    clean_quote = quote.replace("*", "").replace('"', "").replace("Title:", "").strip()
    return clean_quote

def get_unique_nature_img():
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=nature+landscape&orientation=vertical&per_page=100"
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

def create_video(quote_text):
    # Image setting
    clip = ImageClip(get_unique_nature_img()).set_duration(DURATION)
    
    # Text Processing: Quote aur Author ko bada dikhane ke liye
    # Font size increased to 70 for Quote and 50 for Author
    full_display = f"{quote_text}\n\n- {AUTHOR}"
    
    txt_clip = TextClip(full_display, fontsize=70, color='white', font='Arial-Bold', 
                        method='caption', size=(800, None), stroke_color='black', stroke_width=2).set_duration(DURATION).set_position('center')
    
    # Audio download and merge
    search = f"https://freesound.org/apiv2/search/text/?query=piano+soft&token={FREESOUND_KEY}"
    sound_id = requests.get(search).json()['results'][0]['id']
    sound_info = requests.get(f"https://freesound.org/apiv2/sounds/{sound_id}/?token={FREESOUND_KEY}").json()
    with open('music.mp3', 'wb') as f: f.write(requests.get(sound_info['previews']['preview-hq-mp3']).content)
    
    audio = AudioFileClip('music.mp3').subclip(0, DURATION)
    
    # Final Merge
    video = CompositeVideoClip([clip, txt_clip]).set_audio(audio)
    video.write_videofile("final_short.mp4", fps=24, codec="libx264")
    return "final_short.mp4"

def upload_to_catbox(file):
    with open(file, 'rb') as f:
        res = requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
    return res.text.strip()

# Run Sequence
try:
    final_quote = get_ai_quote()
    video_file = create_video(final_quote)
    catbox_url = upload_to_catbox(video_file)

    # Telegram send (Sirf Quote aur Hashtags caption mein)
    caption_text = f"{final_quote}\n\n#motivation #quotes #nature #shorts"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo", 
                  data={"chat_id": TG_CHAT_ID, "video": catbox_url, "caption": caption_text})
    
    requests.post(WEBHOOK_URL, json={"video_url": catbox_url, "quote": final_quote})
    print(f"Video Posted: {catbox_url}")
except Exception as e:
    print(f"Error: {e}")
