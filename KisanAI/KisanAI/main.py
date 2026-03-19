"""
KisanAI — AI Farmer Advisory Platform
FastAPI Full-Stack Application
Run: python main.py
"""

import os
import json
import base64
import random
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── App Setup ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
app = FastAPI(title="KisanAI", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")


# ── Pydantic Models ────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    crop: str = "wheat"
    state: str = "MP"
    soil: str = "black"
    land: float = 2.5

class SoilRequest(BaseModel):
    crop: str = "wheat"
    state: str = "MP"
    soil: str = "black"
    ph: float = 7.0


# ── Static Data ────────────────────────────────────────────
WEATHER_DATA = {
    "MP":  {"temp": 28, "desc": "Partly Cloudy", "humidity": 68, "wind": 12, "rain": 20, "uv": "High",      "alert": "Low rainfall expected. Irrigate wheat within 3 days."},
    "UP":  {"temp": 26, "desc": "Foggy",          "humidity": 82, "wind":  8, "rain": 35, "uv": "Low",       "alert": "Dense fog advisory. Delay spraying operations."},
    "MH":  {"temp": 32, "desc": "Hot & Dry",      "humidity": 45, "wind": 18, "rain":  5, "uv": "Very High", "alert": "Heat wave possible. Irrigate morning or evening only."},
    "PB":  {"temp": 22, "desc": "Clear",           "humidity": 55, "wind": 10, "rain": 10, "uv": "Moderate", "alert": "Good conditions for pesticide spraying today."},
    "RJ":  {"temp": 35, "desc": "Sunny & Hot",    "humidity": 30, "wind": 22, "rain":  2, "uv": "Extreme",  "alert": "Extreme heat. Avoid field work 11 AM – 4 PM."},
    "GJ":  {"temp": 30, "desc": "Warm",            "humidity": 58, "wind": 15, "rain": 12, "uv": "High",     "alert": "Cotton — watch for pink bollworm this week."},
    "HR":  {"temp": 24, "desc": "Pleasant",        "humidity": 60, "wind": 12, "rain": 15, "uv": "Moderate", "alert": "Good wheat growing conditions. Monitor for rust."},
    "AP":  {"temp": 34, "desc": "Humid",           "humidity": 75, "wind": 14, "rain": 40, "uv": "High",     "alert": "Rain expected. Pause fertilizer application."},
}

MARKET_DATA = [
    {"crop": "Wheat",     "hindi": "गेहूँ",    "icon": "🌾", "price": 2340, "change": 45,   "msp": 2275},
    {"crop": "Rice",      "hindi": "धान",      "icon": "🍚", "price": 2183, "change": -12,  "msp": 2183},
    {"crop": "Soybean",   "hindi": "सोयाबीन", "icon": "🫘", "price": 4510, "change": 80,   "msp": 4600},
    {"crop": "Maize",     "hindi": "मक्का",    "icon": "🌽", "price": 1870, "change": 25,   "msp": 1870},
    {"crop": "Mustard",   "hindi": "सरसों",   "icon": "🌿", "price": 5650, "change": 110,  "msp": 5650},
    {"crop": "Cotton",    "hindi": "कपास",    "icon": "☁️", "price": 7020, "change": -30,  "msp": 7121},
    {"crop": "Onion",     "hindi": "प्याज",   "icon": "🧅", "price": 1240, "change": -60,  "msp": None},
    {"crop": "Sugarcane", "hindi": "गन्ना",   "icon": "🪴", "price": 315,  "change": 5,    "msp": 340},
]

PEST_DEMO = [
    {"name": "Aphid (Maahu) Infestation",  "confidence": 91, "description": "Detected aphid colonies on leaf surface. Early stage — treatable.", "treatment": "Spray Imidacloprid 17.8 SL @ 0.5ml/litre. Apply early morning. Repeat after 10 days.", "severity": "Medium"},
    {"name": "Powdery Mildew",             "confidence": 87, "description": "Fungal infection — white powdery patches on leaves.", "treatment": "Spray Mancozeb @ 2.5g/litre or Propiconazole @ 1ml/litre at 10-day intervals.", "severity": "High"},
    {"name": "Leaf Rust (Yellow Rust)",    "confidence": 84, "description": "Yellow-orange pustules on leaves indicating rust infection.", "treatment": "Apply Tebuconazole @ 1ml/litre immediately. Repeat after 14 days.", "severity": "High"},
    {"name": "Healthy Crop — No Issues",   "confidence": 96, "description": "No significant pest or disease detected. Crop appears healthy.", "treatment": "Continue regular monitoring. Preventive fungicide if humidity stays high.", "severity": "None"},
    {"name": "Brown Plant Hopper",         "confidence": 88, "description": "BPH infestation near base of plant. Causes hopper burn.", "treatment": "Drain water 3-4 days. Apply Buprofezin @ 1ml/litre. Use resistant varieties.", "severity": "High"},
]

DEMO_RESPONSES = {
    "en": {
        "yellow":  "🌾 **Yellow Leaf Analysis**\n\nCommon causes:\n\n1. **Nitrogen Deficiency** — Apply 1 bag Urea (50kg/acre) immediately. Best in the morning.\n2. **Powdery Mildew** — Spray Mancozeb @ 2.5g/L if white powder visible.\n3. **Waterlogging** — Ensure drainage if soil is wet.\n\n📅 Best spray time: 6–8 AM to avoid leaf burn.",
        "irrigat": "💧 **Irrigation Advisory**\n\n• Irrigate every **12–14 days** at tillering stage\n• Required: ~5 cm per irrigation\n• Next due: Within 3–4 days\n\n**Method:** Furrow irrigation for black soil.\n⚠️ Low rainfall — don't delay beyond 5 days.",
        "fertil":  "🌱 **Fertilizer Recommendation**\n\n| Nutrient | Product | Dose/acre |\n|---|---|---|\n| N | Urea | 50 kg |\n| P | DAP | 25 kg |\n| K | MOP | 20 kg |\n| Micro | Zinc Sulphate | 5 kg |\n\n**Schedule:** Basal (Full P+K + ⅓N) → 21 DAS (⅓N) → 42 DAS (⅓N)",
        "pest":    "🐛 **Pest Control Guide**\n\n**1. Aphids (Maahu)**\n• Spray Imidacloprid 17.8 SL @ 0.5ml/L\n\n**2. Yellow Rust**\n• Spray Propiconazole @ 1ml/L at first sign\n\n⚠️ Don't spray pesticides within 15 days of harvest.",
        "market":  "📈 **Market Prices (Today)**\n\nMSP Wheat: ₹2,275/quintal\n\n• Bhopal: ₹2,340 ↑\n• Indore: ₹2,310 →\n• Ujjain: ₹2,290 ↓\n\n💡 Register on e-NAM for 5–8% better prices.",
        "season":  "📅 **Sowing Calendar**\n\n**Rabi:** Wheat (Oct 15–Nov 30) · Mustard (Oct 1–31) · Gram (Oct 15–Nov 15)\n\n**Kharif:** Soybean (Jun 15–Jul 15) · Rice (Jun 20–Jul 20) · Maize (Jun 15–Jul 10)",
        "default": "🌾 **General Advisory**\n\n• **Irrigation:** Every 12–15 days at this stage\n• **Fertilizer:** NPK @ 120:60:40 kg/ha in 3 splits\n• **Pest monitoring:** Weekly scouting recommended\n\nTell me your specific problem for detailed advice!",
    },
    "hi": {
        "yellow":  "🌾 **गेहूँ में पीले पत्ते**\n\n1. **नाइट्रोजन की कमी** — तुरंत 1 बोरी यूरिया (50 किग्रा/एकड़) डालें।\n2. **पाउडरी मिल्ड्यू** — मैन्कोज़ेब @ 2.5 ग्राम/लीटर छिड़काव करें।\n\n📅 छिड़काव का सबसे अच्छा समय: सुबह 6–8 बजे।",
        "irrigat": "💧 **सिंचाई सलाह**\n\n• हर **12–14 दिन** में सिंचाई करें\n• प्रति सिंचाई: ~5 सेमी पानी\n• काली मिट्टी में फ़रो विधि उपयुक्त\n\n⚠️ इस सप्ताह कम बारिश — 5 दिन से ज़्यादा देरी न करें।",
        "fertil":  "🌱 **उर्वरक अनुशंसा**\n\n• यूरिया: 50 किग्रा/एकड़\n• DAP: 25 किग्रा/एकड़\n• MOP: 20 किग्रा/एकड़\n• जिंक सल्फेट: 5 किग्रा/एकड़\n\n💡 काली मिट्टी में फॉस्फोरस अच्छा रहता है — DAP अधिक न डालें।",
        "pest":    "🐛 **कीट नियंत्रण**\n\n**1. माहू (Aphids)** — इमिडाक्लोप्रिड @ 0.5 मिली/लीटर\n**2. पीला रतुआ** — प्रोपिकोनाज़ोल @ 1 मिली/लीटर\n\n⚠️ कटाई से 15 दिन पहले कीटनाशक न छिड़कें।",
        "market":  "📈 **आज के मंडी भाव**\n\nMSP गेहूँ: ₹2,275/क्विंटल\n• भोपाल: ₹2,340 ↑\n• इंदौर: ₹2,310 →\n• उज्जैन: ₹2,290 ↓\n\n💡 e-NAM पर पंजीकरण करें।",
        "season":  "📅 **बुवाई कैलेंडर**\n\n**रबी:** गेहूँ (15 अक्टूबर–30 नवम्बर) · सरसों (1–31 अक्टूबर)\n**खरीफ:** सोयाबीन (15 जून–15 जुलाई) · धान (20 जून–20 जुलाई)",
        "default": "🌾 **सामान्य कृषि सलाह**\n\n• **सिंचाई:** हर 12–15 दिन में\n• **खाद:** NPK 120:60:40 किग्रा/हेक्टेयर\n• **निगरानी:** हर हफ्ते कीटों की जाँच\n\nअपनी समस्या विस्तार से बताएं!",
    }
}

SCHEMES = [
    {"name": "PM-KISAN", "benefit": "₹6,000/year direct transfer", "eligibility": "All small & marginal farmers", "link": "https://pmkisan.gov.in"},
    {"name": "Fasal Bima Yojana", "benefit": "Crop insurance at subsidised premium", "eligibility": "Farmers growing notified crops", "link": "https://pmfby.gov.in"},
    {"name": "Kisan Credit Card", "benefit": "Credit up to ₹3 lakh at 4% interest", "eligibility": "Farmers with land records", "link": "https://www.nabard.org"},
    {"name": "e-NAM Portal", "benefit": "Sell directly to buyers pan-India", "eligibility": "Farmers near registered mandis", "link": "https://enam.gov.in"},
    {"name": "Soil Health Card", "benefit": "Free soil testing every 2 years", "eligibility": "All farmers", "link": "https://soilhealth.dac.gov.in"},
    {"name": "PM Krishi Sinchayee", "benefit": "Subsidy on drip/sprinkler irrigation", "eligibility": "Farmers with min 0.5 acre", "link": "https://pmksy.gov.in"},
]

NPK_TABLE = {
    "wheat": {"N": 120, "P": 60, "K": 40},
    "rice": {"N": 100, "P": 50, "K": 50},
    "cotton": {"N": 160, "P": 80, "K": 80},
    "soybean": {"N": 30, "P": 60, "K": 40},
    "sugarcane": {"N": 250, "P": 100, "K": 120},
    "maize": {"N": 120, "P": 60, "K": 40},
    "mustard": {"N": 90, "P": 40, "K": 30},
    "onion": {"N": 100, "P": 50, "K": 75},
}


# ── Routes ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ai_enabled": bool(OPENAI_API_KEY),
    })


@app.get("/api/weather/{state}")
async def get_weather(state: str):
    state = state.upper()
    demo = WEATHER_DATA.get(state, WEATHER_DATA["MP"])
    if WEATHER_API_KEY:
        cities = {"MP": "Bhopal", "UP": "Lucknow", "MH": "Pune", "PB": "Amritsar",
                  "RJ": "Jaipur", "GJ": "Ahmedabad", "HR": "Chandigarh", "AP": "Vijayawada"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={"q": f"{cities.get(state,'Bhopal')},IN", "appid": WEATHER_API_KEY, "units": "metric"}
                )
                if r.status_code == 200:
                    d = r.json()
                    return {"temp": round(d["main"]["temp"]), "desc": d["weather"][0]["description"].title(),
                            "humidity": d["main"]["humidity"], "wind": round(d["wind"]["speed"] * 3.6),
                            "rain": d.get("clouds", {}).get("all", 0), "uv": "See UV app",
                            "alert": demo["alert"], "source": "live"}
        except Exception:
            pass
    return {**demo, "source": "demo"}


@app.get("/api/market")
async def get_market():
    result = []
    for item in MARKET_DATA:
        result.append({**item, "price": item["price"] + random.randint(-20, 25),
                        "change": item["change"] + random.randint(-5, 5)})
    return {"prices": result, "timestamp": "Live (simulated)", "source": "AgMarkNet"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if OPENAI_API_KEY:
        return await _ai_chat(req)
    # Demo mode
    m = req.message.lower()
    lang = req.language if req.language in DEMO_RESPONSES else "en"
    r = DEMO_RESPONSES[lang]
    if any(w in m for w in ["yellow","पीले","colour","color","leaves","पत्ते"]):
        reply = r["yellow"]
    elif any(w in m for w in ["irrigat","water","सिंचाई","पानी"]):
        reply = r["irrigat"]
    elif any(w in m for w in ["fertil","urea","खाद","उर्वरक","dap","npk"]):
        reply = r["fertil"]
    elif any(w in m for w in ["pest","insect","bug","कीट","कीड़","disease","रोग"]):
        reply = r["pest"]
    elif any(w in m for w in ["price","market","sell","भाव","मंडी","rate"]):
        reply = r["market"]
    elif any(w in m for w in ["sow","season","when","बुवाई","मौसम","calendar"]):
        reply = r["season"]
    else:
        reply = r["default"]
    return {"reply": reply, "mode": "demo"}


async def _ai_chat(req: ChatRequest):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    w = WEATHER_DATA.get(req.state.upper(), WEATHER_DATA["MP"])
    lang_inst = "Reply entirely in Hindi (Devanagari script)." if req.language == "hi" else "Reply in clear English."
    system = f"""You are KisanAI, an expert Indian agricultural advisor.
Farmer: State={req.state}, Crop={req.crop}, Soil={req.soil}, Land={req.land} acres
Weather: {w['temp']}°C, {w['desc']}, Humidity={w['humidity']}%
{lang_inst}
Be specific & practical. Use Indian context, emojis, bold headers, bullet points. Max 200 words."""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": req.message}],
            max_tokens=450, temperature=0.7,
        )
        return {"reply": resp.choices[0].message.content, "mode": "ai"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pest-detect")
async def pest_detect(file: UploadFile = File(...), language: str = Form("en")):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    if OPENAI_API_KEY:
        return await _vision_detect(contents, file.content_type or "image/jpeg", language)
    result = random.choice(PEST_DEMO)
    return {**result, "mode": "demo"}


async def _vision_detect(image_bytes: bytes, content_type: str, language: str):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64}"
    lang_note = "Reply in Hindi." if language == "hi" else "Reply in English."
    prompt = f"""Analyze this crop image as an Indian agricultural expert. {lang_note}
Respond ONLY with valid JSON (no markdown fences):
{{"name":"pest or disease name","confidence":85,"description":"2 sentence description","treatment":"2-3 sentence treatment","severity":"None|Low|Medium|High"}}"""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
                {"type": "text", "text": prompt}
            ]}],
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        return {**json.loads(raw), "mode": "ai"}
    except Exception:
        return {**random.choice(PEST_DEMO), "mode": "demo"}


@app.post("/api/soil-advisory")
async def soil_advisory(req: SoilRequest):
    soil_info = {
        "black":    {"description": "Vertisol — high clay, excellent water retention, rich in Ca/Mg.", "crops": ["Cotton","Wheat","Soybean","Chickpea"]},
        "red":      {"description": "Porous, well-drained, deficient in N, P and organic matter.",    "crops": ["Groundnut","Millet","Tobacco","Potato"]},
        "alluvial": {"description": "Highly fertile, ideal for intensive agriculture.",                 "crops": ["Wheat","Rice","Sugarcane","Vegetables"]},
        "sandy":    {"description": "Low water retention, needs frequent irrigation.",                  "crops": ["Groundnut","Watermelon","Carrot","Potato"]},
        "loamy":    {"description": "Ideal balance — best for most crops.",                            "crops": ["All major crops"]},
    }.get(req.soil, {"description": "Mixed soil type.", "crops": ["Consult local KVK"]})

    npk = NPK_TABLE.get(req.crop, {"N": 100, "P": 50, "K": 40})
    if req.ph < 6.0:
        ph_advice = f"pH {req.ph} is acidic. Apply 1–2 tonnes lime per acre."
    elif req.ph > 8.5:
        ph_advice = f"pH {req.ph} is alkaline. Apply gypsum @ 250 kg/acre."
    else:
        ph_advice = f"pH {req.ph} is optimal for most crops. ✅"

    return {
        "soil_info": soil_info, "npk_recommendation": npk,
        "ph_advice": ph_advice,
        "organic_matter": "Apply 5 tonnes FYM or 2 tonnes vermicompost per acre before sowing.",
        "micronutrients": "Apply Zinc Sulphate @ 25 kg/ha and Borax @ 5 kg/ha once every 3 seasons.",
    }


@app.get("/api/schemes")
async def get_schemes():
    return {"schemes": SCHEMES}


@app.get("/health")
async def health():
    return {"status": "ok", "ai_enabled": bool(OPENAI_API_KEY),
            "weather_live": bool(WEATHER_API_KEY), "mode": "AI Active" if OPENAI_API_KEY else "Demo Mode"}


# ── Entry Point ────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    print(f"\n🌾  KisanAI  →  http://localhost:{port}")
    print(f"   AI    : {'✅ OpenAI Active' if OPENAI_API_KEY else '⚡ Demo mode  (add OPENAI_API_KEY to .env)'}")
    print(f"   Weather: {'✅ Live API' if WEATHER_API_KEY else '📦 Built-in data'}\n")
    uvicorn.run("main:app", host=host, port=port, reload=True)
