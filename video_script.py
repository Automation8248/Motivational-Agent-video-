import requests, os, random, json, time
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
import PIL.Image

# ---------- PIL Fix ----------
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# ================== ENV KEYS ==================
PIXABAY_KEY = os.getenv('PIXABAY_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
FREESOUND_API_KEY = os.getenv('FREESOUND_API_KEY')

TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

AUTHOR = "Lucas Hart"
DURATION = 5
HISTORY_FILE = "quotes_history.txt"

# ================== AI CONTENT ==================
def get_ai_content():
    prompt = f"""
Generate UNIQUE motivational content.

Rules:
- Quote max 100 characters
- Title max 40 characters
- Caption 1–2 inspiring lines
- EXACTLY 8 motivational hashtags
- Do NOT repeat previous quotes

Return ONLY JSON:
{{
  "title": "",
  "quote": "",
  "caption": "",
  "hashtags": ["", "", "", "", "", "", "", ""]
}}

Author: {AUTHOR}
"""

    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 300
        }
    )

    raw = res.json()["choices"][0]["message"]["content"]
    if "```" in raw:
        raw = raw.split("```")[1]

    return json.loads(raw)

# ================== PIXABAY IMAGE ==================
def get_bg_image():
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_KEY,
            "q": "nature sunrise mountain",
            "orientation": "vertical",
            "image_type": "photo",
            "per_page": 50,
            "safesearch": "true"
        }
    )
    img_url = random.choice(r.json()["hits"])["largeImageURL"]
    img = requests.get(img_url).content

    with open("bg.jpg", "wb") as f:
        f.write(img)

    return "bg.jpg"

# ================== FREESOUND MUSIC ==================
def get_music():
    headers = {"Authorization": f"Token {FREESOUND_API_KEY}"}
    r = requests.get(
        "https://freesound.org/apiv2/search/text/",
        headers=headers,
        params={
            "query": "motivational cinematic",
            "filter": "duration:[10 TO 60]",
            "page_size": 10
        }
    )

    sound_id = random.choice(r.json()["results"])["id"]
    data = requests.get(
        f"https://freesound.org/apiv2/sounds/{sound_id}/",
        headers=headers
    ).json()

    audio = requests.get(data["previews"]["preview-hq-mp3"]).content
    with open("music.mp3", "wb") as f:
        f.write(audio)

    return "music.mp3"

# ================== VIDEO ==================
def create_video(quote):
    bg = get_bg_image()
    music = get_music()

    clip = (
        ImageClip(bg)
        .set_duration(DURATION)
        .resize(height=1920)
        .fl_image(lambda i: (i * 0.7).astype("uint8"))
    )

    txt = (
        TextClip(
            f"{quote}\n\n- {AUTHOR}",
            fontsize=80,
            color="white",
            font="Arial",
            method="caption",
            size=(850, None)
        )
        .set_position("center")
        .set_duration(DURATION)
    )

    audio = AudioFileClip(music).volumex(0.4).subclip(0, DURATION)

    video = CompositeVideoClip([clip, txt]).set_audio(audio)
    video.write_videofile("final_short.mp4", fps=24, codec="libx264")

    return "final_short.mp4"

# ================== CATBOX ==================
def upload_to_catbox(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f}
        )
    return r.text.strip()

# ================== WEBHOOK ==================
def send_webhook(url):
    requests.post(url, json={"content": url})

# ================== MAIN ==================
if __name__ == "__main__":
    data = get_ai_content()

    video = create_video(data["quote"])
    catbox_link = upload_to_catbox(video)

    # 🔗 Webhook → only link
    if WEBHOOK_URL:
        send_webhook(catbox_link)

    # 📹 Telegram → video + title + caption + hashtags
    telegram_caption = (
        f"🎬 *{data['title']}*\n\n"
        f"{data['caption']}\n\n"
        f"{' '.join(data['hashtags'])}"
    )

    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendVideo",
        data={
            "chat_id": TG_CHAT_ID,
            "caption": telegram_caption,
            "parse_mode": "Markdown"
        },
        files={"video": open(video, "rb")}
    )

    print("✅ ALL DONE")
