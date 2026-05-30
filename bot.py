import asyncio
import nest_asyncio
import os
import json
from telethon import TelegramClient, events
from quart import Quart, Response, request, render_template_string, redirect, url_for, send_from_directory

nest_asyncio.apply()

# --- 1. CONFIGURATION BLOCK ---
API_ID = 31052873
API_HASH = "e71cc6069aefbb722a65e1485353e4de"
BOT_TOKEN = "8899795978:AAH17tIhtrg_f9Wr4_az2Lv2_uvogmrh1BI"
SERVER_URL = "http://127.0.0.1:8089"

OWNER_EMAIL = "akib1aman@gmail.com"
OWNER_PASS = "Farhan899"
ALLOWED_IP = None  

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "web_data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "database.json")
if os.path.exists(DB_PATH):
    try:
        with open(DB_PATH, "r") as f: db_data = json.load(f)
    except: db_data = {}
else:
    db_data = {}

def save_db():
    with open(DB_PATH, "w") as f: json.dump(db_data, f, indent=4)

analytics = {"total_downloads": 148, "online_users": set()}

bot = TelegramClient('stream_session', API_ID, API_HASH)
app = Quart(__name__)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply("⚡ **PlayFlex All-In-One Core Active!**")

@bot.on(events.NewMessage(incoming=True))
async def file_handler(event):
    if event.media and not event.message.message.startswith('/'):
        msg_id = event.id
        chat_id = event.chat_id
        stream_link = f"{SERVER_URL}/video/{chat_id}/{msg_id}/stream.mp4"
        await event.reply(f"✅ **Stream Target Generated:**\n\n`{stream_link}`")

# --- 2. HOME SCREEN LAYOUT ---
USER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PlayFlex Hub</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --accent: #ffcc00; --bg: #09090b; --card-bg: #18181b; --text: #ffffff; }
        body { background-color: var(--bg); color: var(--text); font-family: -apple-system, sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 15px; margin-bottom: 20px; }
        h1 span { color: var(--accent); }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .card { background: var(--card-bg); border-radius: 8px; overflow: hidden; border: 1px solid #27272a; text-decoration: none; color: inherit; display: flex; flex-direction: column; }
        .poster-wrapper { width: 100%; padding-top: 140%; position: relative; background: #27272a; }
        .card img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
        .card-meta { padding: 10px; }
        .card-meta h3 { font-size: 14px; margin: 0 0 5px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PlayFlex <span>Hub</span></h1>
        <a href="/owner-login" style="color: #aaa; text-decoration: none; font-weight: bold; font-size: 14px;">⚙️ Owner</a>
    </div>
    <div class="grid">
        {% for f in all_data.keys() %}
        <a href="/folder/{{ f }}" class="card">
            <div class="poster-wrapper"><img src="/static/{{ f }}.jpg" onerror="this.src='https://via.placeholder.com/300x420?text={{ f }}'"></div>
            <div class="card-meta"><h3>{{ f }}</h3><span style="color: var(--accent); font-size: 11px; font-weight: bold;">Seasons ➔</span></div>
        </a>
        {% endfor %}
    </div>
</body>
</html>
"""

# --- 3. EPISODE VIEW & AUTO ORIENTATION SMART PLAYER ---
FOLDER_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Structure View</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --accent: #ffcc00; --bg: #09090b; --card-bg: #18181b; --text: #ffffff; }
        body { background-color: var(--bg); color: var(--text); font-family: Arial, sans-serif; padding: 15px; margin: 0; }
        .btn-secondary { background: #27272a; color: #e4e4e7; border: 1px solid #3f3f46; padding: 10px 20px; border-radius: 4px; text-decoration: none; display: inline-block; }
        
        .player-container { width: 100%; background: #000; border-radius: 8px; overflow: hidden; margin-bottom: 20px; border: 1px solid #27272a; display: none; }
        .video-wrapper { position: relative; width: 100%; background: #000; }
        video { width: 100%; display: block; background: #000; max-height: 250px; }
        
        video:fullscreen { width: 100vw !important; height: 100vh !important; object-fit: contain !important; }
        @media screen and (orientation: portrait) {
            video:fullscreen { transform: rotate(90deg); width: 100vh !important; height: 100vw !important; }
        }
        
        .action-bar { display: flex; justify-content: space-between; align-items: center; background: #141414; padding: 10px; border-top: 1px solid #27272a; }
        .dl-btn { background: var(--accent); color: #000; padding: 8px 16px; font-size: 13px; font-weight: bold; text-decoration: none; border-radius: 4px; }
        .rotate-btn { background: #27272a; color: var(--accent); padding: 8px 16px; font-size: 13px; font-weight: bold; border-radius: 4px; border: 1px solid #3f3f46; cursor: pointer; }

        .banner { display: flex; gap: 20px; background: var(--card-bg); padding: 15px; border-radius: 8px; align-items: center; margin-bottom: 20px; }
        .banner img { width: 70px; height: 100px; object-fit: cover; border-radius: 6px; }
        .season-section { background: var(--card-bg); border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        .ep-list { display: grid; grid-template-columns: 1fr; gap: 10px; }
        .ep-item { background: #09090b; border: 1px solid #27272a; padding: 14px; border-radius: 4px; display: flex; justify-content: space-between; text-decoration: none; color: #fff; cursor: pointer; font-size: 14px; }
    </style>
    <script>
        function goFullScreenLandscape() {
            var video = document.getElementById('mainPlayer');
            if (video.requestFullscreen) { video.requestFullscreen(); }
            else if (video.webkitRequestFullscreen) { video.webkitRequestFullscreen(); }
            
            if (screen.orientation && screen.orientation.lock) {
                screen.orientation.lock('landscape').catch(function(e) {});
            }
        }

        function playVideoInsideApp(videoUrl, epTitle) {
            var container = document.getElementById('playerContainer');
            var video = document.getElementById('mainPlayer');
            var playerTitle = document.getElementById('playerTitle');
            var downloadLink = document.getElementById('downloadBtn');
            
            var currentHost = window.location.origin;
            var finalUrl = videoUrl;
            if (videoUrl.startsWith('http://127.0.0.1:8089')) {
                finalUrl = videoUrl.replace('http://127.0.0.1:8089', currentHost);
            }

            container.style.display = "block";
            playerTitle.innerText = "🎬 Initializing... " + epTitle;
            downloadLink.href = finalUrl;

            video.src = finalUrl;
            video.load();
            
            video.onloadeddata = function() {
                playerTitle.innerText = "🎬 Now Playing: " + epTitle;
                setTimeout(goFullScreenLandscape, 150);
            };

            video.play().catch(function(e){
                playerTitle.innerText = "⚠️ Error: Click Full Screen to Play";
            });
            window.scrollTo({top: 0, behavior: 'smooth'});
        }
    </script>
</head>
<body>
    <a href="/" class="btn-secondary" style="margin-bottom: 15px;">⬅️ Home</a>
    
    <div class="player-container" id="playerContainer">
        <div class="video-wrapper">
            <video id="mainPlayer" controls playsinline preload="auto" width="100%"></video>
        </div>
        <div class="action-bar">
            <div id="playerTitle" style="font-size: 12px; font-weight: bold; color: #fff; max-width: 50%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">🎬 Selection Box</div>
            <div>
                <button class="rotate-btn" onclick="goFullScreenLandscape()">🔄 Full Screen</button>
                <a id="downloadBtn" href="#" class="dl-btn" download>📥 Download</a>
            </div>
        </div>
    </div>

    <div class="banner">
        <img src="/static/{{ folder_name }}.jpg" onerror="this.src='https://via.placeholder.com/150x210?text={{ folder_name }}'">
        <div><h2 style="margin:0; font-size: 18px;">{{ folder_name_display }}</h2></div>
    </div>

    {% for season, episodes in seasons_data.items() %}
        <div class="season-section">
            <div style="color: var(--accent); font-weight: bold; margin-bottom: 10px;">{{ season }}</div>
            <div class="ep-list">
                {% for ep_title, ep_link in episodes.items() %}
                    <div class="ep-item" onclick="playVideoInsideApp('{{ ep_link }}', '{{ ep_title }}')">
                        <span>▶️ {{ ep_title }}</span>
                        <span style="color: var(--accent); font-size:12px; font-weight: bold;">Watch Box</span>
                    </div>
                {% endfor %}
            </div>
        </div>
    {% endfor %}
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Owner Login</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="background:#09090b; color:white; font-family:sans-serif; padding:30px; text-align:center;">
    <h2>🔒 PlayFlex Owner Access</h2>
    <form action="/verify-owner" method="POST" style="background:#18181b; padding:20px; border-radius:8px; display:inline-block; border:1px solid #27272a;">
        <input type="email" name="email" placeholder="Email" required style="padding:10px; margin:5px; width:200px;"><br>
        <input type="password" name="password" placeholder="Password" required style="padding:10px; margin:5px; width:200px;"><br>
        <button type="submit" style="background:#ffcc00; padding:10px 20px; border:none; border-radius:4px; font-weight:bold; margin-top:10px;">Login Panel</button>
    </form>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Panel</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="background:#09090b; color:white; font-family:sans-serif; padding:15px;">
    <h2>⚙️ PlayFlex Management Board</h2>
    <div style="background:#18181b; padding:15px; border-radius:6px; margin-bottom:20px; border:1px solid #27272a;">
        <h3>Create Series Folder</h3>
        <form action="/create-folder" method="POST" enctype="multipart/form-data">
            <input type="text" name="folder_name" placeholder="Folder Name" required style="padding:8px;">
            <input type="file" name="poster" accept="image/*" required>
            <button type="submit" style="background:#ffcc00; padding:8px; border:none; font-weight:bold;">Create</button>
        </form>
    </div>
    <div style="background:#18181b; padding:15px; border-radius:6px; border:1px solid #27272a;">
        <h3>Bulk Link Ingestion</h3>
        <form action="/add-bulk-links" method="POST">
            <select name="target_folder" style="padding:8px;">
                {% for f in folders %} <option value="{{f}}">{{f}}</option> {% endfor %}
            </select><br><br>
            <input type="text" name="season_name" placeholder="Season (e.g. Season 01)" required style="padding:8px;"><br><br>
            <input type="text" name="episode_prefix" placeholder="Prefix (e.g. Episode)" required style="padding:8px;"><br><br>
            <textarea name="bulk_links" placeholder="Paste HTTP stream links here (one per line)" rows="5" style="width:100%; max-width:400px;"></textarea><br><br>
            <button type="submit" style="background:#ffcc00; padding:8px; border:none; font-weight:bold;">Execute Ingestion</button>
        </form>
    </div>
    <br><a href="/" style="color:#ffcc00; text-decoration:none;">⬅️ Back to Hub</a>
</body>
</html>
"""

@app.before_request
async def track_analytics(): analytics["online_users"].add(request.remote_addr)

@app.route('/')
async def home(): return await render_template_string(USER_HTML, all_data=db_data)

@app.route('/folder/<string:folder_name>')
async def view_folder(folder_name):
    if folder_name not in db_data: return redirect(url_for('home'))
    seasons_dict = db_data[folder_name].get("seasons", {})
    total_eps = sum(len(eps) for eps in seasons_dict.values())
    return await render_template_string(FOLDER_PAGE_HTML, folder_name=folder_name, folder_name_display=folder_name, seasons_data=seasons_dict, total_episodes=total_eps)

@app.route('/owner-login')
async def owner_login(): return await render_template_string(LOGIN_HTML)

@app.route('/verify-owner', methods=['POST'])
async def verify_owner():
    global ALLOWED_IP
    form = await request.form
    if form.get('email') == OWNER_EMAIL and form.get('password') == OWNER_PASS:
        ALLOWED_IP = request.remote_addr
        return redirect(url_for('admin_panel'))
    return "Invalid Credentials", 401

@app.route('/admin-panel')
async def admin_panel():
    if request.remote_addr != ALLOWED_IP: return "Unauthorized Access Blocked", 403
    return await render_template_string(ADMIN_HTML, folders=list(db_data.keys()), all_data=db_data)

@app.route('/create-folder', methods=['POST'])
async def create_folder():
    if request.remote_addr != ALLOWED_IP: return "Unauthorized", 403
    form = await request.form
    files = await request.files
    name = form.get('folder_name').strip()
    poster = files.get('poster')
    if name and name not in db_data:
        db_data[name] = {"seasons": {}}
        if poster: await poster.save(os.path.join(STATIC_DIR, f"{name}.jpg"))
        save_db()
    return redirect(url_for('admin_panel'))

@app.route('/add-bulk-links', methods=['POST'])
async def add_bulk_links():
    if request.remote_addr != ALLOWED_IP: return "Unauthorized", 403
    form = await request.form
    folder = form.get('target_folder')
    season = form.get('season_name').strip()
    prefix = form.get('episode_prefix').strip()
    raw_links = form.get('bulk_links')
    if folder in db_data and raw_links:
        if "seasons" not in db_data[folder]: db_data[folder]["seasons"] = {}
        if season not in db_data[folder]["seasons"]: db_data[folder]["seasons"][season] = {}
        links_list = [lnk.strip() for lnk in raw_links.split('\n') if lnk.strip().startswith('http')]
        start_count = len(db_data[folder]["seasons"][season]) + 1
        for i, link in enumerate(links_list):
            db_data[folder]["seasons"][season][f"{prefix} : {start_count + i:02d} S1 » Quality : 1080p » Audio : Hindi | #Official 1"] = link
        save_db()
    return redirect(url_for('admin_panel'))

@app.route('/static/<path:filename>')
async def send_static(filename): return await send_from_directory(STATIC_DIR, filename)

@app.route('/video/<int:chat_id>/<int:msg_id>/stream.mp4')
async def stream_server(chat_id, msg_id):
    try:
        message = await bot.get_messages(chat_id, ids=msg_id)
        if not message or not message.media: return "File Error", 404
        
        file_size = message.media.document.size
        range_header = request.headers.get('Range', None)
        start, end = 0, file_size - 1
        status_code = 200
        
        if range_header:
            status_code = 206
            clean_rh = range_header.replace('bytes=', '')
            ranges = clean_rh.split('-')
            if ranges[0]: start = int(ranges[0])
            if ranges[1]: end = int(ranges[1])
            
        chunk_size = end - start + 1
        
        async def data_generator():
            async for chunk in bot.iter_download(message.media, offset=start, stride=chunk_size, chunk_size=6144*1024): 
                yield chunk

        headers = {
            'Content-Type': 'video/mp4',
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Content-Length': str(chunk_size),
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive'
        }
        return Response(data_generator(), status=status_code, headers=headers)
    except Exception as e: return f"Error: {str(e)}", 500

async def start_everything():
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 PlayFlex Unified Engine Active on Port 8089")
    await app.run_task(host="0.0.0.0", port=8089)

if __name__ == '__main__':
    asyncio.run(start_everything())
  
