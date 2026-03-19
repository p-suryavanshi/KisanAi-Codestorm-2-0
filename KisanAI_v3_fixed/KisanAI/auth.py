"""
KisanAI — Auth System (JSON file-based, no database needed)
"""
import json, hashlib, os, secrets
from pathlib import Path
from datetime import datetime

DB_FILE = Path(__file__).parent / "users.json"

def _load():
    if not DB_FILE.exists():
        DB_FILE.write_text(json.dumps({"users": {}, "sessions": {}}))
    return json.loads(DB_FILE.read_text())

def _save(data):
    DB_FILE.write_text(json.dumps(data, indent=2))

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register(name: str, mobile: str, password: str, state: str = "MP", crop: str = "wheat"):
    data = _load()
    if mobile in data["users"]:
        return None, "Mobile number already registered"
    data["users"][mobile] = {
        "name": name, "mobile": mobile,
        "password": _hash(password),
        "state": state, "crop": crop,
        "soil": "black", "land": 2.5,
        "joined": datetime.now().strftime("%d %b %Y"),
        "chats": [], "badges": ["🌱 New Farmer"]
    }
    _save(data)
    return data["users"][mobile], None

def login(mobile: str, password: str):
    data = _load()
    user = data["users"].get(mobile)
    if not user or user["password"] != _hash(password):
        return None, None, "Invalid mobile or password"
    token = secrets.token_hex(32)
    data["sessions"][token] = mobile
    _save(data)
    return user, token, None

def get_user(token: str):
    if not token: return None
    data = _load()
    mobile = data["sessions"].get(token)
    if not mobile: return None
    return data["users"].get(mobile)

def update_profile(token: str, updates: dict):
    data = _load()
    mobile = data["sessions"].get(token)
    if not mobile: return None
    allowed = ["name", "state", "crop", "soil", "land"]
    for k, v in updates.items():
        if k in allowed:
            data["users"][mobile][k] = v
    _save(data)
    return data["users"][mobile]

def save_chat(token: str, question: str, answer: str):
    data = _load()
    mobile = data["sessions"].get(token)
    if not mobile: return
    chat = {"q": question, "a": answer[:300], "time": datetime.now().strftime("%d %b %H:%M")}
    data["users"][mobile].setdefault("chats", []).append(chat)
    # Keep last 50 chats
    data["users"][mobile]["chats"] = data["users"][mobile]["chats"][-50:]
    # Award badges
    n = len(data["users"][mobile]["chats"])
    badges = data["users"][mobile].get("badges", ["🌱 New Farmer"])
    if n >= 5 and "🌾 Active Farmer" not in badges: badges.append("🌾 Active Farmer")
    if n >= 20 and "⭐ Smart Farmer" not in badges: badges.append("⭐ Smart Farmer")
    if n >= 50 and "🏆 KisanAI Expert" not in badges: badges.append("🏆 KisanAI Expert")
    data["users"][mobile]["badges"] = badges
    _save(data)

def logout(token: str):
    data = _load()
    data["sessions"].pop(token, None)
    _save(data)

def get_all_users_count():
    data = _load()
    return len(data["users"])
