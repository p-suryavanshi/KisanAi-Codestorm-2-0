"""
KisanAI v3 — Fixed & Complete
Run: python main.py
"""
import os, json, base64, random, re
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
import auth as Auth

load_dotenv()
BASE_DIR = Path(__file__).parent
app = FastAPI(title="KisanAI", version="3.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
WEATHER_KEY = os.getenv("WEATHER_API_KEY", "")

# ── Pydantic Models ────────────────────────────────────────
class ChatReq(BaseModel):
    message: str
    language: str = "en"
    crop: str = "wheat"
    state: str = "MP"
    soil: str = "black"
    land: float = 2.5
    city: str = ""
    save_history: bool = True

class SoilReq(BaseModel):
    crop: str = "wheat"
    state: str = "MP"
    soil: str = "black"
    ph: float = 7.0

class WaterReq(BaseModel):
    crop: str = "wheat"
    stage: str = "tillering"
    area: float = 2.5
    soil: str = "black"

class RegisterReq(BaseModel):
    name: str; mobile: str; password: str
    state: str = "MP"; crop: str = "wheat"

class LoginReq(BaseModel):
    mobile: str; password: str

class ProfileUpd(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    crop: Optional[str] = None
    soil: Optional[str] = None
    land: Optional[float] = None
    city: Optional[str] = None

# ── All Indian States ──────────────────────────────────────
ALL_STATES = {
    "MP": {"name": "Madhya Pradesh", "city": "Bhopal"},
    "UP": {"name": "Uttar Pradesh",  "city": "Lucknow"},
    "MH": {"name": "Maharashtra",    "city": "Pune"},
    "PB": {"name": "Punjab",         "city": "Amritsar"},
    "RJ": {"name": "Rajasthan",      "city": "Jaipur"},
    "GJ": {"name": "Gujarat",        "city": "Ahmedabad"},
    "HR": {"name": "Haryana",        "city": "Chandigarh"},
    "AP": {"name": "Andhra Pradesh", "city": "Vijayawada"},
    "TN": {"name": "Tamil Nadu",     "city": "Chennai"},
    "KA": {"name": "Karnataka",      "city": "Bengaluru"},
    "WB": {"name": "West Bengal",    "city": "Kolkata"},
    "BR": {"name": "Bihar",          "city": "Patna"},
    "OR": {"name": "Odisha",         "city": "Bhubaneswar"},
    "AS": {"name": "Assam",          "city": "Guwahati"},
    "JH": {"name": "Jharkhand",      "city": "Ranchi"},
    "CG": {"name": "Chhattisgarh",   "city": "Raipur"},
    "UK": {"name": "Uttarakhand",    "city": "Dehradun"},
    "HP": {"name": "Himachal Pradesh","city": "Shimla"},
    "KL": {"name": "Kerala",         "city": "Thiruvananthapuram"},
    "TS": {"name": "Telangana",      "city": "Hyderabad"},
    "GA": {"name": "Goa",            "city": "Panaji"},
    "MN": {"name": "Manipur",        "city": "Imphal"},
    "MZ": {"name": "Mizoram",        "city": "Aizawl"},
    "NL": {"name": "Nagaland",       "city": "Kohima"},
    "TR": {"name": "Tripura",        "city": "Agartala"},
    "SK": {"name": "Sikkim",         "city": "Gangtok"},
    "AR": {"name": "Arunachal Pradesh","city": "Itanagar"},
    "ML": {"name": "Meghalaya",      "city": "Shillong"},
    "DL": {"name": "Delhi",          "city": "New Delhi"},
    "JK": {"name": "Jammu & Kashmir","city": "Srinagar"},
}

# ── Weather Data (all states) ──────────────────────────────
WEATHER_DATA = {
    "MP":  {"temp":28,"feels":31,"desc":"Partly Cloudy","humidity":68,"wind":12,"rain":20,"uv":"High","alert":"Low rainfall expected. Irrigate wheat within 3 days.","forecast":[{"day":"Today","icon":"⛅","high":28,"low":19},{"day":"Thu","icon":"☀️","high":30,"low":20},{"day":"Fri","icon":"🌧️","high":24,"low":17},{"day":"Sat","icon":"⛅","high":26,"low":18},{"day":"Sun","icon":"☀️","high":29,"low":21}]},
    "UP":  {"temp":26,"feels":28,"desc":"Foggy","humidity":82,"wind":8,"rain":35,"uv":"Low","alert":"Dense fog advisory. Delay spraying operations.","forecast":[{"day":"Today","icon":"🌫️","high":26,"low":15},{"day":"Thu","icon":"🌫️","high":25,"low":14},{"day":"Fri","icon":"⛅","high":27,"low":16},{"day":"Sat","icon":"☀️","high":28,"low":17},{"day":"Sun","icon":"⛅","high":26,"low":15}]},
    "MH":  {"temp":32,"feels":36,"desc":"Hot & Dry","humidity":45,"wind":18,"rain":5,"uv":"Very High","alert":"Heat wave possible. Irrigate morning or evening only.","forecast":[{"day":"Today","icon":"☀️","high":32,"low":22},{"day":"Thu","icon":"☀️","high":34,"low":23},{"day":"Fri","icon":"☀️","high":33,"low":22},{"day":"Sat","icon":"⛅","high":30,"low":20},{"day":"Sun","icon":"🌧️","high":27,"low":19}]},
    "PB":  {"temp":22,"feels":23,"desc":"Clear","humidity":55,"wind":10,"rain":10,"uv":"Moderate","alert":"Good conditions for pesticide spraying today.","forecast":[{"day":"Today","icon":"🌤️","high":22,"low":12},{"day":"Thu","icon":"☀️","high":24,"low":13},{"day":"Fri","icon":"☀️","high":25,"low":14},{"day":"Sat","icon":"⛅","high":22,"low":12},{"day":"Sun","icon":"🌤️","high":21,"low":11}]},
    "RJ":  {"temp":35,"feels":40,"desc":"Sunny & Hot","humidity":30,"wind":22,"rain":2,"uv":"Extreme","alert":"Extreme heat. Avoid field work 11 AM – 4 PM.","forecast":[{"day":"Today","icon":"🌞","high":35,"low":22},{"day":"Thu","icon":"🌞","high":37,"low":23},{"day":"Fri","icon":"☀️","high":36,"low":22},{"day":"Sat","icon":"⛅","high":32,"low":20},{"day":"Sun","icon":"☀️","high":34,"low":21}]},
    "GJ":  {"temp":30,"feels":33,"desc":"Warm","humidity":58,"wind":15,"rain":12,"uv":"High","alert":"Cotton — watch for pink bollworm this week.","forecast":[{"day":"Today","icon":"🌤️","high":30,"low":20},{"day":"Thu","icon":"☀️","high":32,"low":21},{"day":"Fri","icon":"⛅","high":29,"low":19},{"day":"Sat","icon":"🌧️","high":26,"low":18},{"day":"Sun","icon":"⛅","high":28,"low":19}]},
    "HR":  {"temp":24,"feels":25,"desc":"Pleasant","humidity":60,"wind":12,"rain":15,"uv":"Moderate","alert":"Good wheat growing conditions. Monitor for rust.","forecast":[{"day":"Today","icon":"🌤️","high":24,"low":13},{"day":"Thu","icon":"☀️","high":26,"low":14},{"day":"Fri","icon":"⛅","high":23,"low":12},{"day":"Sat","icon":"🌧️","high":20,"low":11},{"day":"Sun","icon":"⛅","high":22,"low":12}]},
    "AP":  {"temp":34,"feels":38,"desc":"Humid","humidity":75,"wind":14,"rain":40,"uv":"High","alert":"Rain expected. Pause fertilizer application.","forecast":[{"day":"Today","icon":"🌦️","high":34,"low":24},{"day":"Thu","icon":"🌧️","high":30,"low":22},{"day":"Fri","icon":"🌧️","high":28,"low":21},{"day":"Sat","icon":"⛅","high":31,"low":22},{"day":"Sun","icon":"🌤️","high":33,"low":23}]},
    "TN":  {"temp":33,"feels":37,"desc":"Hot & Humid","humidity":72,"wind":16,"rain":30,"uv":"High","alert":"High humidity — watch for fungal diseases in rice.","forecast":[{"day":"Today","icon":"🌦️","high":33,"low":24},{"day":"Thu","icon":"🌧️","high":30,"low":23},{"day":"Fri","icon":"⛅","high":31,"low":23},{"day":"Sat","icon":"🌤️","high":32,"low":24},{"day":"Sun","icon":"☀️","high":34,"low":25}]},
    "KA":  {"temp":29,"feels":32,"desc":"Partly Cloudy","humidity":62,"wind":13,"rain":25,"uv":"High","alert":"Good spray window this morning.","forecast":[{"day":"Today","icon":"⛅","high":29,"low":20},{"day":"Thu","icon":"⛅","high":30,"low":21},{"day":"Fri","icon":"🌧️","high":27,"low":19},{"day":"Sat","icon":"⛅","high":28,"low":20},{"day":"Sun","icon":"☀️","high":31,"low":21}]},
    "WB":  {"temp":27,"feels":30,"desc":"Cloudy","humidity":78,"wind":11,"rain":45,"uv":"Low","alert":"Rain likely — avoid field operations today.","forecast":[{"day":"Today","icon":"🌧️","high":27,"low":20},{"day":"Thu","icon":"🌧️","high":26,"low":19},{"day":"Fri","icon":"⛅","high":28,"low":20},{"day":"Sat","icon":"☀️","high":30,"low":21},{"day":"Sun","icon":"⛅","high":29,"low":20}]},
    "BR":  {"temp":25,"feels":27,"desc":"Hazy","humidity":70,"wind":9,"rain":20,"uv":"Moderate","alert":"Moderate fog in morning. Scout for stem borer.","forecast":[{"day":"Today","icon":"🌫️","high":25,"low":14},{"day":"Thu","icon":"⛅","high":26,"low":15},{"day":"Fri","icon":"☀️","high":28,"low":16},{"day":"Sat","icon":"☀️","high":27,"low":15},{"day":"Sun","icon":"⛅","high":25,"low":14}]},
    "KL":  {"temp":31,"feels":36,"desc":"Hot & Humid","humidity":85,"wind":18,"rain":50,"uv":"High","alert":"Heavy rain alert. Drain waterlogged fields.","forecast":[{"day":"Today","icon":"🌧️","high":31,"low":24},{"day":"Thu","icon":"🌧️","high":29,"low":23},{"day":"Fri","icon":"🌧️","high":28,"low":23},{"day":"Sat","icon":"⛅","high":30,"low":24},{"day":"Sun","icon":"🌤️","high":32,"low":24}]},
    "TS":  {"temp":33,"feels":37,"desc":"Sunny","humidity":50,"wind":15,"rain":8,"uv":"Very High","alert":"High UV today. Avoid field work 11 AM–3 PM.","forecast":[{"day":"Today","icon":"☀️","high":33,"low":22},{"day":"Thu","icon":"☀️","high":35,"low":23},{"day":"Fri","icon":"⛅","high":32,"low":22},{"day":"Sat","icon":"🌧️","high":28,"low":20},{"day":"Sun","icon":"⛅","high":30,"low":21}]},
}
# Default for states without specific data
DEFAULT_WEATHER = {"temp":28,"feels":31,"desc":"Partly Cloudy","humidity":65,"wind":12,"rain":20,"uv":"Moderate","alert":"Monitor crops regularly. Check for pest activity.","forecast":[{"day":"Today","icon":"⛅","high":28,"low":18},{"day":"Thu","icon":"☀️","high":30,"low":19},{"day":"Fri","icon":"⛅","high":27,"low":17},{"day":"Sat","icon":"🌧️","high":24,"low":16},{"day":"Sun","icon":"☀️","high":29,"low":18}]}

# ── Market Data ────────────────────────────────────────────
MARKET_DATA = [
    {"crop":"Wheat",    "hindi":"गेहूँ",    "icon":"🌾","price":2340,"change":45,  "msp":2275,"trend":[2180,2210,2240,2260,2295,2320,2340]},
    {"crop":"Rice",     "hindi":"धान",      "icon":"🍚","price":2183,"change":-12, "msp":2183,"trend":[2200,2195,2190,2188,2185,2190,2183]},
    {"crop":"Soybean",  "hindi":"सोयाबीन", "icon":"🫘","price":4510,"change":80,  "msp":4600,"trend":[4200,4280,4350,4400,4430,4480,4510]},
    {"crop":"Maize",    "hindi":"मक्का",    "icon":"🌽","price":1870,"change":25,  "msp":1870,"trend":[1780,1800,1820,1835,1850,1860,1870]},
    {"crop":"Mustard",  "hindi":"सरसों",   "icon":"🌿","price":5650,"change":110, "msp":5650,"trend":[5200,5300,5380,5450,5520,5590,5650]},
    {"crop":"Cotton",   "hindi":"कपास",    "icon":"☁️","price":7020,"change":-30, "msp":7121,"trend":[7200,7180,7150,7100,7080,7050,7020]},
    {"crop":"Onion",    "hindi":"प्याज",   "icon":"🧅","price":1240,"change":-60, "msp":None, "trend":[1600,1520,1450,1380,1320,1280,1240]},
    {"crop":"Sugarcane","hindi":"गन्ना",   "icon":"🪴","price":315, "change":5,   "msp":340,  "trend":[300,302,305,308,310,312,315]},
    {"crop":"Gram",     "hindi":"चना",     "icon":"🫛","price":5440,"change":90,  "msp":5440,"trend":[5100,5180,5250,5310,5370,5410,5440]},
    {"crop":"Tomato",   "hindi":"टमाटर",   "icon":"🍅","price":980, "change":-120,"msp":None, "trend":[1400,1300,1200,1150,1100,1050,980]},
    {"crop":"Potato",   "hindi":"आलू",     "icon":"🥔","price":1150,"change":30,  "msp":None, "trend":[1000,1050,1080,1100,1120,1140,1150]},
    {"crop":"Groundnut","hindi":"मूंगफली", "icon":"🥜","price":5800,"change":60,  "msp":5850,"trend":[5500,5580,5640,5680,5720,5770,5800]},
]

# ── Pest Detection Demo Results ────────────────────────────
PEST_DEMO = [
    {"name":"Aphid (Maahu) Infestation","confidence":91,"description":"Dense aphid colonies on leaf surface and stems. Early stage — treatable.","treatment":"Spray Imidacloprid 17.8 SL @ 0.5ml/litre. Apply early morning. Repeat after 10 days if needed.","severity":"Medium","organic":"Neem oil @ 5ml/litre or release ladybird beetles as biocontrol."},
    {"name":"Powdery Mildew","confidence":87,"description":"White powdery fungal patches on upper leaf surface. Spreads in humid conditions.","treatment":"Spray Mancozeb @ 2.5g/litre or Propiconazole @ 1ml/litre at 10-day intervals.","severity":"High","organic":"Baking soda solution (5g/litre) or diluted milk (1:9). Remove affected leaves."},
    {"name":"Leaf Rust (Yellow Rust)","confidence":84,"description":"Yellow-orange pustules indicating systemic rust infection.","treatment":"Apply Tebuconazole @ 1ml/litre immediately. Repeat after 14 days.","severity":"High","organic":"Remove infected debris. Use resistant varieties next season."},
    {"name":"Healthy Crop ✓","confidence":96,"description":"No significant pest or disease detected. Crop appears vigorous and healthy.","treatment":"Continue regular monitoring. Preventive fungicide if humidity stays >80% for 3+ days.","severity":"None","organic":"Maintain field hygiene. Apply compost to boost plant immunity."},
    {"name":"Brown Plant Hopper","confidence":88,"description":"BPH infestation at base causing hopper burn and lodging.","treatment":"Drain water 3–4 days. Apply Buprofezin @ 1ml/litre.","severity":"High","organic":"Maintain alternate wetting/drying. Use light traps at night."},
]

# ── Crop Calendar (expanded) ───────────────────────────────
CROP_CALENDAR = {
    "wheat":     {"sow":"Nov–Dec","grow":"Dec–Feb","harvest":"Mar–Apr","duration":"120–150 days","seasons":["Rabi"],"bestVariety":"HD-2967, GW-322, WH-1105, DBW-187","irrigations":5,"water_mm":450},
    "rice":      {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Oct–Nov","duration":"110–145 days","seasons":["Kharif"],"bestVariety":"Pusa Basmati 1121, Swarna, MTU-7029, IR-64","irrigations":20,"water_mm":1200},
    "cotton":    {"sow":"Apr–Jun","grow":"Jul–Sep","harvest":"Oct–Jan","duration":"150–180 days","seasons":["Kharif"],"bestVariety":"Bt Cotton (MRC-7017, RCH-650), MCU-5","irrigations":8,"water_mm":700},
    "soybean":   {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Oct","duration":"90–110 days","seasons":["Kharif"],"bestVariety":"JS-335, MAUS-81, NRC-7, JS-9560","irrigations":3,"water_mm":450},
    "sugarcane": {"sow":"Feb–Mar","grow":"Apr–Dec","harvest":"Nov–Mar","duration":"10–12 months","seasons":["Annual"],"bestVariety":"Co-0238, CoJ-64, CoLk-94184, CoSe-01424","irrigations":35,"water_mm":1800},
    "maize":     {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Sep–Oct","duration":"85–95 days","seasons":["Kharif","Rabi"],"bestVariety":"NK-6240, DKC-9144, Vivek-QPM-9, HQPM-1","irrigations":6,"water_mm":500},
    "mustard":   {"sow":"Oct–Nov","grow":"Nov–Jan","harvest":"Feb–Mar","duration":"110–140 days","seasons":["Rabi"],"bestVariety":"Pusa Bold, RH-30, GSC-6, Kranti","irrigations":3,"water_mm":300},
    "onion":     {"sow":"Oct–Nov","grow":"Nov–Feb","harvest":"Mar–Apr","duration":"110–130 days","seasons":["Rabi"],"bestVariety":"Agrifound White, Nasik Red, N-53, Bhima Raj","irrigations":12,"water_mm":500},
    "gram":      {"sow":"Oct–Nov","grow":"Nov–Jan","harvest":"Feb–Mar","duration":"90–110 days","seasons":["Rabi"],"bestVariety":"JG-11, Vijay, KWR-108, JAKI-9218","irrigations":2,"water_mm":300},
    "tomato":    {"sow":"Jun–Jul (Kharif), Oct–Nov (Rabi)","grow":"Jul–Nov","harvest":"Sep–Jan","duration":"60–90 days","seasons":["Kharif","Rabi"],"bestVariety":"Pusa Ruby, Arka Vikas, CO-3, Naveen","irrigations":15,"water_mm":600},
    "potato":    {"sow":"Oct–Nov","grow":"Nov–Jan","harvest":"Jan–Mar","duration":"80–120 days","seasons":["Rabi"],"bestVariety":"Kufri Jyoti, Kufri Badshah, Kufri Sindhuri, Atlantic","irrigations":8,"water_mm":450},
    "groundnut": {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Oct–Nov","duration":"100–120 days","seasons":["Kharif"],"bestVariety":"GG-20, TAG-24, JL-24, K-6","irrigations":4,"water_mm":500},
}

# ── Water Requirements (stage-wise, all crops) ─────────────
# Stage names must match the dropdown values in HTML exactly
WATER_REQ = {
    "wheat":     {"sowing":5,"tillering":6,"jointing":7,"heading":6,"maturity":4,"total":550},
    "rice":      {"sowing":8,"tillering":7,"jointing":7,"heading":6,"maturity":5,"total":1200},
    "cotton":    {"sowing":4,"tillering":6,"jointing":8,"heading":7,"maturity":4,"total":700},
    "soybean":   {"sowing":4,"tillering":5,"jointing":6,"heading":5,"maturity":3,"total":450},
    "sugarcane": {"sowing":6,"tillering":8,"jointing":10,"heading":8,"maturity":5,"total":1800},
    "maize":     {"sowing":4,"tillering":6,"jointing":8,"heading":6,"maturity":4,"total":500},
    "mustard":   {"sowing":4,"tillering":5,"jointing":6,"heading":5,"maturity":3,"total":300},
    "onion":     {"sowing":5,"tillering":5,"jointing":6,"heading":6,"maturity":4,"total":500},
    "gram":      {"sowing":3,"tillering":4,"jointing":5,"heading":4,"maturity":3,"total":300},
    "tomato":    {"sowing":4,"tillering":6,"jointing":7,"heading":7,"maturity":5,"total":600},
    "potato":    {"sowing":4,"tillering":6,"jointing":7,"heading":6,"maturity":4,"total":450},
    "groundnut": {"sowing":4,"tillering":5,"jointing":6,"heading":5,"maturity":4,"total":500},
}

# ── NPK Table (all crops) ──────────────────────────────────
NPK_TABLE = {
    "wheat":{"N":120,"P":60,"K":40},"rice":{"N":100,"P":50,"K":50},
    "cotton":{"N":160,"P":80,"K":80},"soybean":{"N":30,"P":60,"K":40},
    "sugarcane":{"N":250,"P":100,"K":120},"maize":{"N":120,"P":60,"K":40},
    "mustard":{"N":90,"P":40,"K":30},"onion":{"N":100,"P":50,"K":75},
    "gram":{"N":25,"P":50,"K":30},"tomato":{"N":120,"P":60,"K":80},
    "potato":{"N":150,"P":100,"K":120},"groundnut":{"N":25,"P":50,"K":50},
}

# ── Yield Table (base quintal/acre) ───────────────────────
YIELD_TABLE = {
    "wheat":22,"rice":28,"cotton":8,"soybean":12,"sugarcane":280,
    "maize":25,"mustard":10,"onion":80,"gram":8,"tomato":120,
    "potato":100,"groundnut":10,
}

# ── News ───────────────────────────────────────────────────
AGRI_NEWS = [
    {"title":"PM-KISAN 19th installment released — ₹2,000 credited to 9.4 crore farmers","time":"2 hrs ago","category":"Policy","icon":"💰"},
    {"title":"Wheat MSP hiked to ₹2,425/quintal for 2025–26 Rabi season","time":"1 day ago","category":"Market","icon":"📈"},
    {"title":"New high-yield wheat variety 'Raj-4238' released for Central India","time":"2 days ago","category":"Technology","icon":"🌾"},
    {"title":"Locust warning issued for Rajasthan and Gujarat borders","time":"3 days ago","category":"Alert","icon":"⚠️"},
    {"title":"e-NAM platform crosses ₹3 lakh crore in trade — new record","time":"4 days ago","category":"Market","icon":"🏆"},
    {"title":"Drip irrigation subsidy increased to 60% for small farmers in 15 states","time":"5 days ago","category":"Scheme","icon":"💧"},
    {"title":"ICAR releases drought-resistant soybean variety for Vidarbha region","time":"6 days ago","category":"Technology","icon":"🔬"},
    {"title":"Kisan Credit Card limit raised to ₹5 lakh for short-term loans","time":"1 week ago","category":"Scheme","icon":"💳"},
]

SCHEMES = [
    {"name":"PM-KISAN","icon":"💰","benefit":"₹6,000/year in 3 installments","eligibility":"All small & marginal farmers","link":"https://pmkisan.gov.in","color":"#2d6a4f"},
    {"name":"Fasal Bima Yojana","icon":"🛡️","benefit":"Crop insurance at 1.5–5% premium","eligibility":"Farmers growing notified crops","link":"https://pmfby.gov.in","color":"#1e4d6b"},
    {"name":"Kisan Credit Card","icon":"💳","benefit":"Credit up to ₹5 lakh at 4% interest","eligibility":"All farmers & sharecroppers","link":"https://www.nabard.org","color":"#4a1942"},
    {"name":"e-NAM Portal","icon":"📱","benefit":"Sell pan-India, 5–8% better prices","eligibility":"Farmers near registered mandis","link":"https://enam.gov.in","color":"#7a3b00"},
    {"name":"Soil Health Card","icon":"🧪","benefit":"Free soil testing + NPK guide","eligibility":"All farmers","link":"https://soilhealth.dac.gov.in","color":"#4a3b00"},
    {"name":"PM Krishi Sinchayee","icon":"💧","benefit":"55–60% subsidy on drip irrigation","eligibility":"Farmers with min 0.5 acre land","link":"https://pmksy.gov.in","color":"#003d4d"},
]

# ── Helper: build dynamic demo response ───────────────────
def make_demo_response(req: ChatReq, key: str) -> str:
    crop = req.crop.title()
    state = ALL_STATES.get(req.state.upper(), {}).get("name", req.state)
    soil = req.soil.title()
    land = req.land
    city = req.city or ALL_STATES.get(req.state.upper(), {}).get("city", state)
    cal = CROP_CALENDAR.get(req.crop.lower(), {})
    npk = NPK_TABLE.get(req.crop.lower(), {"N":100,"P":50,"K":40})
    water = WATER_REQ.get(req.crop.lower(), WATER_REQ["wheat"])
    is_hi = req.language == "hi"

    responses = {
        "yellow": {
            "en": f"🌾 **Yellow Leaf Analysis — {crop}**\n\n**Most likely: Nitrogen Deficiency**\n\n• Apply Urea (50 kg/acre) immediately\n• Best time: Morning 6–8 AM on {soil} soil in {state}\n• Also check: Powdery Mildew (white powder → Mancozeb @ 2.5g/L), Waterlogging (check drainage)\n\n📅 Recovery expected: 7–10 days after application",
            "hi": f"🌾 **{crop} में पीले पत्तों का विश्लेषण**\n\n**सबसे संभावित: नाइट्रोजन की कमी**\n\n• तुरंत यूरिया (50 किग्रा/एकड़) डालें\n• {state} में {soil} मिट्टी पर सुबह 6–8 बजे डालें\n• यह भी जांचें: पाउडरी मिल्ड्यू (मैन्कोज़ेब @ 2.5 ग्राम/लीटर)\n\n📅 7–10 दिन में सुधार दिखेगा",
        },
        "irrigat": {
            "en": f"💧 **Irrigation Guide — {crop} ({land} acres, {state})**\n\n• Irrigate every **{water.get('tillering', 6)//1}-{water.get('jointing', 7)//1} days** at current stage\n• Water per irrigation: {water.get('tillering', 6)} cm on {soil} soil\n• Total for your farm: {round(water.get('tillering',6)*land,1)} cm\n• Best time: Early morning (saves 30% water)\n• Seasonal total: {water['total']} mm\n\n⚠️ Monitor soil moisture before each irrigation",
            "hi": f"💧 **सिंचाई सलाह — {crop} ({land} एकड़, {state})**\n\n• हर {water.get('tillering', 6)}-{water.get('jointing', 7)} दिन में सिंचाई करें\n• {soil} मिट्टी पर {water.get('tillering', 6)} सेमी पानी दें\n• आपके खेत के लिए: {round(water.get('tillering',6)*land,1)} सेमी\n• सुबह सिंचाई करें — 30% पानी बचता है\n\n⚠️ हर सिंचाई से पहले मिट्टी की नमी जांचें",
        },
        "fertil": {
            "en": f"🌱 **Fertilizer Schedule — {crop} ({state}, {soil} soil)**\n\n| Nutrient | Dose/acre | When |\n|---|---|---|\n| N (Urea) | {npk['N']//3} kg × 3 | Basal + 21 + 42 DAS |\n| P (DAP) | {npk['P']//2} kg | Basal |\n| K (MOP) | {npk['K']} kg | Basal |\n| Zinc Sulphate | 5 kg | Once/season |\n\n💰 Est. cost: ₹{npk['N']*18 + npk['P']*27 + npk['K']*16}/acre",
            "hi": f"🌱 **उर्वरक कार्यक्रम — {crop} ({state}, {soil} मिट्टी)**\n\n• नाइट्रोजन (यूरिया): {npk['N']//3} किग्रा × 3 बार\n• फॉस्फोरस (DAP): {npk['P']//2} किग्रा (बुवाई पर)\n• पोटाश (MOP): {npk['K']} किग्रा (बुवाई पर)\n• जिंक सल्फेट: 5 किग्रा/एकड़\n\n💰 अनुमानित लागत: ₹{npk['N']*18 + npk['P']*27 + npk['K']*16}/एकड़",
        },
        "pest": {
            "en": f"🐛 **Pest Management — {crop} in {state}**\n\n**🔴 Watch for this season:**\n• Aphids: Imidacloprid 17.8 SL @ 0.5ml/L\n• Rust/Blight: Propiconazole @ 1ml/L\n• Caterpillars: Chlorpyrifos @ 2ml/L\n\n**✅ Prevention:**\n• Weekly scouting — 5 plants per 100m row\n• Sticky traps to monitor pest pressure\n• Seed treatment with Carbendazim\n\n⚠️ Don't spray within 15 days of harvest",
            "hi": f"🐛 **कीट प्रबंधन — {crop} ({state})**\n\n**🔴 इस मौसम में सावधान:**\n• माहू: इमिडाक्लोप्रिड @ 0.5 मिली/लीटर\n• रतुआ/झुलसा: प्रोपिकोनाज़ोल @ 1 मिली/लीटर\n• इल्ली: क्लोरपाइरीफॉस @ 2 मिली/लीटर\n\n✅ निवारण: साप्ताहिक निगरानी करें\n\n⚠️ कटाई से 15 दिन पहले कीटनाशक न छिड़कें",
        },
        "market": {
            "en": f"📈 **Market Report — {crop} in {state}**\n\n• Today's range: ₹{YIELD_TABLE.get(req.crop.lower(), 20)*95}–{YIELD_TABLE.get(req.crop.lower(), 20)*108}/quintal\n• Nearest mandi: {city}\n• MSP (if applicable): ₹{NPK_TABLE.get(req.crop.lower(),{}).get('N',0)*18}/quintal\n\n**Best strategy:**\n• Store 3–4 weeks post-harvest for better price\n• Use e-NAM for pan-India buyers (5–8% better)\n• Check AgMarkNet app daily for price updates",
            "hi": f"📈 **बाज़ार रिपोर्ट — {crop} ({state})**\n\n• आज का भाव: ₹{YIELD_TABLE.get(req.crop.lower(), 20)*95}–{YIELD_TABLE.get(req.crop.lower(), 20)*108}/क्विंटल\n• नज़दीकी मंडी: {city}\n\n**बेस्ट स्ट्रेटेजी:**\n• कटाई के 3–4 हफ्ते बाद बेचें — भाव अच्छा मिलेगा\n• e-NAM पर पंजीकरण करें — 5–8% अधिक मिलेगा",
        },
        "season": {
            "en": f"📅 **Sowing Calendar — {crop} in {state}**\n\n• Sowing: {cal.get('sow', 'Varies by region')}\n• Growing: {cal.get('grow', 'N/A')}\n• Harvest: {cal.get('harvest', 'N/A')}\n• Duration: {cal.get('duration', 'N/A')}\n• Irrigations needed: {cal.get('irrigations', 'N/A')}\n\n**Best varieties for {state}:** {cal.get('bestVariety', 'Consult local KVK')}\n\n💡 Contact your nearest KVK for state-specific variety recommendations",
            "hi": f"📅 **बुवाई कैलेंडर — {crop} ({state})**\n\n• बुवाई: {cal.get('sow', 'क्षेत्र के अनुसार')}\n• उगाई: {cal.get('grow', 'N/A')}\n• कटाई: {cal.get('harvest', 'N/A')}\n• अवधि: {cal.get('duration', 'N/A')}\n\n**{state} के लिए बेस्ट किस्में:** {cal.get('bestVariety', 'नज़दीकी KVK से पूछें')}\n\n💡 राज्य-विशिष्ट किस्मों के लिए KVK से संपर्क करें",
        },
        "default": {
            "en": f"🌾 **Advisory for your {crop} farm — {state}**\n\n**Your profile:** {soil} soil · {land} acres · {city}\n\n**This week's priorities:**\n✅ Check soil moisture — irrigate if <50% capacity\n✅ Weekly pest scouting (5 plants/100m row)\n✅ Monitor weather — spray window check\n\n**Expected yield:** {YIELD_TABLE.get(req.crop.lower(), 20)}–{int(YIELD_TABLE.get(req.crop.lower(), 20)*1.15)} q/acre\n**Est. revenue:** ₹{int(YIELD_TABLE.get(req.crop.lower(), 20)*land*2300):,}/season\n\nAsk about pest control, fertilizer, irrigation or market prices!",
            "hi": f"🌾 **{crop} खेती सलाह — {state}**\n\n**आपका प्रोफाइल:** {soil} मिट्टी · {land} एकड़ · {city}\n\n**इस हफ्ते करें:**\n✅ मिट्टी की नमी जांचें\n✅ कीट निगरानी (5 पौधे/100 मीटर)\n✅ मौसम चेक करें\n\n**अनुमानित उपज:** {YIELD_TABLE.get(req.crop.lower(), 20)}–{int(YIELD_TABLE.get(req.crop.lower(), 20)*1.15)} क्विंटल/एकड़\n\nकीट, खाद, सिंचाई या बाज़ार के बारे में पूछें!",
        },
    }
    lang_key = "hi" if is_hi else "en"
    return responses.get(key, responses["default"])[lang_key]

def get_demo_reply(req: ChatReq) -> str:
    m = req.message.lower()
    if any(w in m for w in ["yellow","पीले","colour","color","pale","पीला","wilting"]):
        return make_demo_response(req, "yellow")
    if any(w in m for w in ["irrigat","water","सिंचाई","पानी","drip","sprinkler","बारिश"]):
        return make_demo_response(req, "irrigat")
    if any(w in m for w in ["fertil","urea","खाद","उर्वरक","dap","npk","manure","compost","nutrient"]):
        return make_demo_response(req, "fertil")
    if any(w in m for w in ["pest","insect","bug","कीट","कीड़","disease","रोग","spray","fungus","worm"]):
        return make_demo_response(req, "pest")
    if any(w in m for w in ["price","market","sell","भाव","मंडी","rate","msp","profit","income"]):
        return make_demo_response(req, "market")
    if any(w in m for w in ["sow","season","when","बुवाई","मौसम","calendar","plant","variety","किस्म"]):
        return make_demo_response(req, "season")
    return make_demo_response(req, "default")

# ── Routes ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, "ai_enabled": bool(OPENAI_KEY),
        "states": ALL_STATES
    })

@app.get("/api/states")
async def get_states():
    return {"states": ALL_STATES}

@app.get("/api/weather/{state}")
async def get_weather(state: str, city: str = ""):
    state = state.upper()
    demo = WEATHER_DATA.get(state, DEFAULT_WEATHER)
    query_city = city or ALL_STATES.get(state, {}).get("city", "Bhopal")
    if WEATHER_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get("https://api.openweathermap.org/data/2.5/weather",
                    params={"q": f"{query_city},IN", "appid": WEATHER_KEY, "units": "metric"})
                if r.status_code == 200:
                    d = r.json()
                    return {**demo, "temp": round(d["main"]["temp"]),
                            "feels": round(d["main"]["feels_like"]),
                            "desc": d["weather"][0]["description"].title(),
                            "humidity": d["main"]["humidity"],
                            "wind": round(d["wind"]["speed"] * 3.6),
                            "city": query_city, "source": "live"}
        except: pass
    return {**demo, "city": query_city, "source": "demo"}

@app.get("/api/market")
async def get_market():
    result = []
    for item in MARKET_DATA:
        # Bounded fluctuation — price never goes below 50% of base
        fluct = random.randint(-15, 20)
        new_price = max(int(item["price"] * 0.5), item["price"] + fluct)
        new_change = item["change"] + random.randint(-5, 5)
        new_trend = item["trend"][1:] + [new_price]
        result.append({**item, "price": new_price, "change": new_change, "trend": new_trend})
    return {"prices": result, "updated": datetime.now().strftime("%d %b %Y %I:%M %p"), "source": "AgMarkNet (simulated)"}

@app.post("/api/chat")
async def chat(req: ChatReq):
    if OPENAI_KEY:
        return await _ai_chat(req)
    return {"reply": get_demo_reply(req), "mode": "demo"}

@app.post("/api/chat/auth")
async def chat_auth(req: ChatReq, kisanai_token: str = Cookie(default=None)):
    user = Auth.get_user(kisanai_token)
    if user:
        # Always use account profile values (fix: don't use "or" which treats defaults as falsy)
        req.crop  = user.get("crop", req.crop)
        req.state = user.get("state", req.state)
        req.soil  = user.get("soil", req.soil)
        req.land  = user.get("land", req.land)
        req.city  = user.get("city", req.city)
    if OPENAI_KEY:
        result = await _ai_chat(req)
    else:
        result = {"reply": get_demo_reply(req), "mode": "demo"}
    if user and kisanai_token and req.save_history:
        Auth.save_chat(kisanai_token, req.message, result.get("reply", ""))
    return result

async def _ai_chat(req: ChatReq):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_KEY)
    w = WEATHER_DATA.get(req.state.upper(), DEFAULT_WEATHER)
    state_name = ALL_STATES.get(req.state.upper(), {}).get("name", req.state)
    city = req.city or ALL_STATES.get(req.state.upper(), {}).get("city", "")
    lang_inst = "Reply entirely in Hindi (Devanagari script)." if req.language == "hi" else "Reply in English."
    system = f"""You are KisanAI, India's most advanced agricultural advisor.
Farmer profile: State={state_name}, City={city}, Crop={req.crop}, Soil={req.soil} soil, Land={req.land} acres
Current weather: {w['temp']}°C feels {w.get('feels',w['temp'])}°C, {w['desc']}, Humidity={w['humidity']}%, Rain={w['rain']}%
{lang_inst}
Be specific and practical. Use the actual crop name (not just 'wheat'). Give real product names, doses, timings.
Use emojis, bold headers, tables where helpful. Keep under 220 words."""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},{"role":"user","content":req.message}],
            max_tokens=500, temperature=0.7)
        return {"reply": resp.choices[0].message.content, "mode": "ai"}
    except Exception as e:
        # Fall back to demo on AI error
        return {"reply": get_demo_reply(req) + f"\n\n_(AI unavailable: {str(e)[:60]})_", "mode": "demo"}

@app.post("/api/pest-detect")
async def pest_detect(file: UploadFile = File(...), language: str = Form("en"), crop: str = Form("unknown")):
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "No file uploaded")
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 10MB.")
    ct = file.content_type or "image/jpeg"
    if not ct.startswith("image/"):
        raise HTTPException(400, "Only image files are accepted (JPG, PNG, WEBP)")
    if OPENAI_KEY:
        return await _vision_detect(contents, ct, language, crop)
    result = random.choice(PEST_DEMO)
    return {**result, "mode": "demo", "crop_context": crop}

async def _vision_detect(image_bytes, content_type, language, crop="unknown"):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_KEY)
    b64 = base64.b64encode(image_bytes).decode()
    lang_note = "Reply in Hindi (Devanagari)." if language == "hi" else "Reply in English."
    prompt = f"""You are an expert Indian agricultural plant pathologist.
The farmer grows {crop}. {lang_note}
Analyze this crop image and respond ONLY with valid JSON (no markdown):
{{"name":"pest or disease name","confidence":85,"description":"2 sentence description of what you see","treatment":"2-3 sentence chemical treatment recommendation with dosage","severity":"None|Low|Medium|High","organic":"1-2 sentence organic/natural alternative"}}"""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:{content_type};base64,{b64}","detail":"low"}},
                {"type":"text","text":prompt}
            ]}], max_tokens=400)
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json","").replace("```","").strip()
        return {**json.loads(raw), "mode":"ai", "crop_context": crop}
    except Exception as e:
        return {**random.choice(PEST_DEMO), "mode":"demo", "error": str(e)[:80]}

@app.post("/api/soil-advisory")
async def soil_advisory(req: SoilReq):
    soil_info = {
        "black":    {"desc":"Vertisol — high clay, excellent water retention, self-mulching.","ph_range":"7.5–8.5","om":"Medium","drainage":"Poor to moderate","best_for":"Cotton, Wheat, Soybean"},
        "red":      {"desc":"Porous, well-drained, low in N, P and organic matter.","ph_range":"6.0–7.0","om":"Low","drainage":"Good","best_for":"Groundnut, Millet, Tobacco"},
        "alluvial": {"desc":"Highly fertile, ideal for intensive agriculture, rich in K.","ph_range":"6.5–7.5","om":"Medium-High","drainage":"Moderate","best_for":"Wheat, Rice, Sugarcane"},
        "sandy":    {"desc":"Low water/nutrient retention, needs frequent inputs.","ph_range":"6.0–7.0","om":"Very Low","drainage":"Excellent","best_for":"Groundnut, Watermelon, Carrot"},
        "loamy":    {"desc":"Ideal balance of sand, silt and clay — best for most crops.","ph_range":"6.0–7.0","om":"High","drainage":"Good","best_for":"All major crops"},
    }
    npk = NPK_TABLE.get(req.crop.lower(), {"N":100,"P":50,"K":40})
    crop_is_known = req.crop.lower() in NPK_TABLE
    ph = req.ph
    if ph < 6.0:
        ph_advice = f"pH {ph:.1f} is acidic. Apply lime @ 1–2 tonnes/acre to raise pH. Re-test in 2 months."
    elif ph > 8.5:
        ph_advice = f"pH {ph:.1f} is alkaline. Apply gypsum @ 250 kg/acre + organic matter."
    elif 6.0 <= ph <= 6.5:
        ph_advice = f"pH {ph:.1f} is slightly acidic. Ideal for most crops. Light lime if below 6.0."
    else:
        ph_advice = f"pH {ph:.1f} is optimal ✅ — ideal range for most Indian crops."
    # Score based on actual inputs
    base_score = 70
    soil_bonus = {"loamy":15,"alluvial":12,"black":8,"red":2,"sandy":-5}.get(req.soil, 5)
    ph_bonus = 10 if 6.2 <= ph <= 7.2 else (5 if 5.8 <= ph <= 7.8 else -5)
    score = min(98, max(35, base_score + soil_bonus + ph_bonus + random.randint(-3,3)))
    soil = soil_info.get(req.soil, soil_info["loamy"])
    return {
        "soil_profile": soil, "npk": npk, "ph_advice": ph_advice,
        "organic": "Apply 5 tonnes FYM or 2 tonnes vermicompost per acre before sowing.",
        "micro": "Zinc Sulphate @ 25 kg/ha + Borax @ 5 kg/ha once every 3 seasons.",
        "score": score,
        "crop_known": crop_is_known,
        "note": "" if crop_is_known else f"'{req.crop}' is a custom crop — using general NPK values. Consult your local KVK for precise recommendations."
    }

@app.post("/api/water-calculator")
async def water_calculator(req: WaterReq):
    wr = WATER_REQ.get(req.crop.lower(), WATER_REQ["wheat"])
    stage_need = wr.get(req.stage, 6)
    soil_factor = {"black":0.85,"alluvial":0.90,"loamy":0.90,"red":1.10,"sandy":1.30}.get(req.soil, 1.0)
    water_per_acre = round(stage_need * soil_factor, 1)
    total_water = round(water_per_acre * req.area, 1)
    # Duration: assume flow rate of 1 litre/sec/acre (approx 36 cm/hr coverage)
    duration_hrs = round(total_water / 3.6, 1)
    next_days = {"sowing":14,"tillering":12,"jointing":10,"heading":12,"maturity":16}.get(req.stage, 12)
    crop_is_known = req.crop.lower() in WATER_REQ
    return {
        "crop": req.crop, "stage": req.stage, "soil": req.soil,
        "water_per_acre": water_per_acre, "total_for_farm": total_water,
        "unit": "cm", "duration_hrs": duration_hrs,
        "next_irrigation_days": next_days,
        "total_seasonal_mm": wr["total"],
        "tip": "Irrigate 5–7 AM for lowest evaporation loss. Saves 30–40% water.",
        "crop_known": crop_is_known,
        "note": "" if crop_is_known else f"Using general estimates for '{req.crop}'. Check with local agronomist."
    }

@app.get("/api/crop-calendar/{crop}")
async def crop_calendar(crop: str):
    c = crop.lower().strip()
    cal = CROP_CALENDAR.get(c)
    if cal:
        return {**cal, "found": True, "crop": crop}
    # Generic fallback for unknown crops
    return {
        "found": False, "crop": crop,
        "sow": "Depends on region and season",
        "grow": "Typically 60–180 days",
        "harvest": "Depends on variety",
        "duration": "Consult local KVK for exact schedule",
        "seasons": ["Varies"],
        "bestVariety": "Contact your nearest Krishi Vigyan Kendra (KVK) for local variety recommendations",
        "irrigations": "Varies by crop",
        "water_mm": "N/A",
        "note": f"'{crop}' is not in our database. Showing general guidance. Visit https://kvk.icar.gov.in for crop-specific advice."
    }

@app.get("/api/yield-estimate")
async def yield_estimate(crop: str = "wheat", soil: str = "black", land: float = 2.5, irrigation: int = 3):
    base = YIELD_TABLE.get(crop.lower(), 20)
    soil_m = {"black":1.0,"alluvial":1.1,"loamy":1.05,"red":0.9,"sandy":0.85}.get(soil, 1.0)
    irr_m = min(1.0, 0.65 + irrigation * 0.07)
    yield_q = round(base * soil_m * irr_m, 1)
    total = round(yield_q * land, 1)
    # FIX: was dividing by 100 incorrectly — price is per quintal
    price = next((m["price"] for m in MARKET_DATA if m["crop"].lower() == crop.lower()), 2300)
    revenue = int(yield_q * land * price)   # ← FIXED (was /100)
    crop_known = crop.lower() in YIELD_TABLE
    return {
        "crop": crop, "yield_per_acre": yield_q, "total_yield": total,
        "estimated_revenue": revenue, "price_per_quintal": price,
        "crop_known": crop_known,
        "note": "" if crop_known else f"Using general yield estimate for '{crop}'. Actual yield varies by variety and management."
    }

@app.get("/api/news")
async def get_news():
    return {"news": AGRI_NEWS, "updated": datetime.now().strftime("%d %b %Y %I:%M %p")}

@app.get("/api/schemes")
async def get_schemes():
    return {"schemes": SCHEMES}

# ── Auth Pages ─────────────────────────────────────────────
@app.get("/login",     response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register",  response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, kisanai_token: str = Cookie(default=None)):
    user = Auth.get_user(kisanai_token)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user,
        "ai_enabled": bool(OPENAI_KEY),
        "total_users": Auth.get_all_users_count(),
        "states": ALL_STATES,
    })

# ── Auth API ───────────────────────────────────────────────
@app.post("/api/auth/register")
async def api_register(req: RegisterReq):
    name = req.name.strip()
    mobile = re.sub(r'\D', '', req.mobile)
    if len(name) < 2:
        return JSONResponse({"error": "Name must be at least 2 characters"}, status_code=400)
    if len(mobile) < 10:
        return JSONResponse({"error": "Enter a valid 10-digit mobile number"}, status_code=400)
    if len(req.password) < 6:
        return JSONResponse({"error": "Password must be at least 6 characters"}, status_code=400)
    user, err = Auth.register(name, mobile, req.password, req.state, req.crop)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    _, token, _ = Auth.login(mobile, req.password)
    resp = JSONResponse({"success": True, "name": user["name"], "redirect": "/dashboard"})
    resp.set_cookie("kisanai_token", token, max_age=30*24*3600, httponly=True, samesite="lax")
    return resp

@app.post("/api/auth/login")
async def api_login(req: LoginReq):
    mobile = re.sub(r'\D', '', req.mobile)
    user, token, err = Auth.login(mobile, req.password)
    if err:
        return JSONResponse({"error": err}, status_code=401)
    resp = JSONResponse({"success": True, "name": user["name"], "redirect": "/dashboard"})
    resp.set_cookie("kisanai_token", token, max_age=30*24*3600, httponly=True, samesite="lax")
    return resp

@app.post("/api/auth/logout")
async def api_logout(kisanai_token: str = Cookie(default=None)):
    if kisanai_token:
        Auth.logout(kisanai_token)
    resp = JSONResponse({"success": True})
    resp.delete_cookie("kisanai_token")
    return resp

@app.get("/api/auth/me")
async def api_me(kisanai_token: str = Cookie(default=None)):
    user = Auth.get_user(kisanai_token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    return {
        "name": user["name"], "mobile": user["mobile"],
        "state": user.get("state","MP"), "crop": user.get("crop","wheat"),
        "soil": user.get("soil","black"), "land": user.get("land",2.5),
        "city": user.get("city",""), "joined": user["joined"],
        "badges": user.get("badges",[]), "chat_count": len(user.get("chats",[])),
        "recent_chats": user.get("chats",[])[-10:]
    }

@app.post("/api/auth/profile")
async def api_profile(req: ProfileUpd, kisanai_token: str = Cookie(default=None)):
    user = Auth.get_user(kisanai_token)
    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    updates = {k: v for k, v in req.model_dump().items() if v is not None}  # FIX: req.dict() deprecated
    updated = Auth.update_profile(kisanai_token, updates)
    return {"success": True, "user": updated}

@app.get("/health")
async def health():
    return {"status":"ok","version":"3.0","ai":bool(OPENAI_KEY),"mode":"AI Active" if OPENAI_KEY else "Demo Mode","states": len(ALL_STATES),"crops":len(CROP_CALENDAR)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    print(f"\n🌾  KisanAI v3  →  http://localhost:{port}")
    print(f"   Mode   : {'✅ AI Active' if OPENAI_KEY else '⚡ Demo Mode'}")
    print(f"   States : {len(ALL_STATES)} | Crops: {len(CROP_CALENDAR)}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
