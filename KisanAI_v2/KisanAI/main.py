"""
KisanAI v2 — Advanced AI Farmer Advisory Platform
FastAPI Full-Stack | Run: python main.py
"""
import os, json, base64, random
from pathlib import Path
from datetime import datetime
import httpx
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent
app = FastAPI(title="KisanAI v2", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# ── Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str; language: str = "en"; crop: str = "wheat"
    state: str = "MP"; soil: str = "black"; land: float = 2.5

class SoilRequest(BaseModel):
    crop: str = "wheat"; state: str = "MP"; soil: str = "black"; ph: float = 7.0

class WaterRequest(BaseModel):
    crop: str = "wheat"; stage: str = "tillering"; area: float = 2.5; soil: str = "black"

# ── Static Data ────────────────────────────────────────────
WEATHER_DATA = {
    "MP":  {"temp":28,"feels":31,"desc":"Partly Cloudy","humidity":68,"wind":12,"rain":20,"uv":"High","visibility":10,"alert":"Low rainfall expected. Irrigate wheat within 3 days.","forecast":[{"day":"Today","icon":"⛅","high":28,"low":19},{"day":"Thu","icon":"☀️","high":30,"low":20},{"day":"Fri","icon":"🌧️","high":24,"low":17},{"day":"Sat","icon":"⛅","high":26,"low":18},{"day":"Sun","icon":"☀️","high":29,"low":21}]},
    "UP":  {"temp":26,"feels":28,"desc":"Foggy","humidity":82,"wind":8,"rain":35,"uv":"Low","visibility":3,"alert":"Dense fog advisory. Delay spraying operations.","forecast":[{"day":"Today","icon":"🌫️","high":26,"low":15},{"day":"Thu","icon":"🌫️","high":25,"low":14},{"day":"Fri","icon":"⛅","high":27,"low":16},{"day":"Sat","icon":"☀️","high":28,"low":17},{"day":"Sun","icon":"⛅","high":26,"low":15}]},
    "MH":  {"temp":32,"feels":36,"desc":"Hot & Dry","humidity":45,"wind":18,"rain":5,"uv":"Very High","visibility":15,"alert":"Heat wave possible. Irrigate morning or evening only.","forecast":[{"day":"Today","icon":"☀️","high":32,"low":22},{"day":"Thu","icon":"☀️","high":34,"low":23},{"day":"Fri","icon":"☀️","high":33,"low":22},{"day":"Sat","icon":"⛅","high":30,"low":20},{"day":"Sun","icon":"🌧️","high":27,"low":19}]},
    "PB":  {"temp":22,"feels":23,"desc":"Clear","humidity":55,"wind":10,"rain":10,"uv":"Moderate","visibility":20,"alert":"Good conditions for pesticide spraying today.","forecast":[{"day":"Today","icon":"🌤️","high":22,"low":12},{"day":"Thu","icon":"☀️","high":24,"low":13},{"day":"Fri","icon":"☀️","high":25,"low":14},{"day":"Sat","icon":"⛅","high":22,"low":12},{"day":"Sun","icon":"🌤️","high":21,"low":11}]},
    "RJ":  {"temp":35,"feels":40,"desc":"Sunny & Hot","humidity":30,"wind":22,"rain":2,"uv":"Extreme","visibility":18,"alert":"Extreme heat. Avoid field work 11 AM – 4 PM.","forecast":[{"day":"Today","icon":"🌞","high":35,"low":22},{"day":"Thu","icon":"🌞","high":37,"low":23},{"day":"Fri","icon":"☀️","high":36,"low":22},{"day":"Sat","icon":"⛅","high":32,"low":20},{"day":"Sun","icon":"☀️","high":34,"low":21}]},
    "GJ":  {"temp":30,"feels":33,"desc":"Warm","humidity":58,"wind":15,"rain":12,"uv":"High","visibility":12,"alert":"Cotton — watch for pink bollworm this week.","forecast":[{"day":"Today","icon":"🌤️","high":30,"low":20},{"day":"Thu","icon":"☀️","high":32,"low":21},{"day":"Fri","icon":"⛅","high":29,"low":19},{"day":"Sat","icon":"🌧️","high":26,"low":18},{"day":"Sun","icon":"⛅","high":28,"low":19}]},
    "HR":  {"temp":24,"feels":25,"desc":"Pleasant","humidity":60,"wind":12,"rain":15,"uv":"Moderate","visibility":16,"alert":"Good wheat growing conditions. Monitor for rust.","forecast":[{"day":"Today","icon":"🌤️","high":24,"low":13},{"day":"Thu","icon":"☀️","high":26,"low":14},{"day":"Fri","icon":"⛅","high":23,"low":12},{"day":"Sat","icon":"🌧️","high":20,"low":11},{"day":"Sun","icon":"⛅","high":22,"low":12}]},
    "AP":  {"temp":34,"feels":38,"desc":"Humid","humidity":75,"wind":14,"rain":40,"uv":"High","visibility":8,"alert":"Rain expected. Pause fertilizer application.","forecast":[{"day":"Today","icon":"🌦️","high":34,"low":24},{"day":"Thu","icon":"🌧️","high":30,"low":22},{"day":"Fri","icon":"🌧️","high":28,"low":21},{"day":"Sat","icon":"⛅","high":31,"low":22},{"day":"Sun","icon":"🌤️","high":33,"low":23}]},
}

MARKET_DATA = [
    {"crop":"Wheat","hindi":"गेहूँ","icon":"🌾","price":2340,"change":45,"msp":2275,"trend":[2180,2210,2240,2260,2295,2320,2340]},
    {"crop":"Rice","hindi":"धान","icon":"🍚","price":2183,"change":-12,"msp":2183,"trend":[2200,2195,2190,2188,2185,2190,2183]},
    {"crop":"Soybean","hindi":"सोयाबीन","icon":"🫘","price":4510,"change":80,"msp":4600,"trend":[4200,4280,4350,4400,4430,4480,4510]},
    {"crop":"Maize","hindi":"मक्का","icon":"🌽","price":1870,"change":25,"msp":1870,"trend":[1780,1800,1820,1835,1850,1860,1870]},
    {"crop":"Mustard","hindi":"सरसों","icon":"🌿","price":5650,"change":110,"msp":5650,"trend":[5200,5300,5380,5450,5520,5590,5650]},
    {"crop":"Cotton","hindi":"कपास","icon":"☁️","price":7020,"change":-30,"msp":7121,"trend":[7200,7180,7150,7100,7080,7050,7020]},
    {"crop":"Onion","hindi":"प्याज","icon":"🧅","price":1240,"change":-60,"msp":None,"trend":[1600,1520,1450,1380,1320,1280,1240]},
    {"crop":"Sugarcane","hindi":"गन्ना","icon":"🪴","price":315,"change":5,"msp":340,"trend":[300,302,305,308,310,312,315]},
    {"crop":"Gram","hindi":"चना","icon":"🫛","price":5440,"change":90,"msp":5440,"trend":[5100,5180,5250,5310,5370,5410,5440]},
    {"crop":"Tomato","hindi":"टमाटर","icon":"🍅","price":980,"change":-120,"msp":None,"trend":[1400,1300,1200,1150,1100,1050,980]},
]

PEST_DEMO = [
    {"name":"Aphid (Maahu) Infestation","confidence":91,"description":"Dense aphid colonies detected on leaf surface and stems. Early infestation stage — highly treatable.","treatment":"Spray Imidacloprid 17.8 SL @ 0.5ml/litre water. Apply early morning. Repeat after 10 days if needed. Avoid during flowering.","severity":"Medium","organic":"Spray neem oil @ 5ml/litre or release ladybird beetles as biocontrol."},
    {"name":"Powdery Mildew (Choorni Asita)","confidence":87,"description":"White powdery fungal patches on upper leaf surface. Spreads rapidly in humid conditions.","treatment":"Spray Mancozeb @ 2.5g/litre or Propiconazole @ 1ml/litre. Apply 2–3 sprays at 10-day intervals. Ensure air circulation.","severity":"High","organic":"Spray baking soda solution (5g/litre) or diluted milk (1:9 ratio). Remove affected leaves."},
    {"name":"Leaf Rust (Yellow Rust)","confidence":84,"description":"Yellow-orange pustules on leaf surface indicating systemic rust infection.","treatment":"Apply Tebuconazole @ 1ml/litre water immediately. Repeat after 14 days. Avoid overhead irrigation.","severity":"High","organic":"Remove infected plant debris. Use resistant varieties in next season. Avoid excessive nitrogen."},
    {"name":"Healthy Crop ✓","confidence":96,"description":"No significant pest or disease detected. Crop appears vigorous and healthy.","treatment":"Continue regular monitoring. Consider preventive fungicide if humidity stays above 80% for 3+ days.","severity":"None","organic":"Maintain field hygiene. Apply compost to boost plant immunity."},
    {"name":"Brown Plant Hopper","confidence":88,"description":"BPH infestation at base of plants causing hopper burn and lodging.","treatment":"Drain water 3–4 days. Apply Buprofezin @ 1ml/litre or Thiamethoxam @ 0.2g/litre.","severity":"High","organic":"Maintain alternate wetting/drying. Avoid excess nitrogen. Use light traps at night."},
]

CROP_CALENDAR = {
    "wheat":    {"sow":"Nov–Dec","grow":"Dec–Feb","harvest":"Mar–Apr","duration":"120–150 days","seasons":["Rabi"],"bestVariety":"HD-2967, GW-322, WH-1105","irrigations":5},
    "rice":     {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Oct–Nov","duration":"110–145 days","seasons":["Kharif"],"bestVariety":"Pusa Basmati 1121, Swarna, MTU-7029","irrigations":20},
    "cotton":   {"sow":"Apr–Jun","grow":"Jul–Sep","harvest":"Oct–Jan","duration":"150–180 days","seasons":["Kharif"],"bestVariety":"Bt Cotton varieties, MCU-5","irrigations":8},
    "soybean":  {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Oct","duration":"90–110 days","seasons":["Kharif"],"bestVariety":"JS-335, MAUS-81, NRC-7","irrigations":3},
    "sugarcane":{"sow":"Feb–Mar","grow":"Apr–Dec","harvest":"Nov–Mar","duration":"10–12 months","seasons":["Annual"],"bestVariety":"Co-0238, CoJ-64, CoLk-94184","irrigations":35},
    "maize":    {"sow":"Jun–Jul","grow":"Jul–Sep","harvest":"Sep–Oct","duration":"85–95 days","seasons":["Kharif","Rabi"],"bestVariety":"NK-6240, DKC-9144, Vivek-QPM-9","irrigations":6},
    "mustard":  {"sow":"Oct–Nov","grow":"Nov–Jan","harvest":"Feb–Mar","duration":"110–140 days","seasons":["Rabi"],"bestVariety":"Pusa Bold, RH-30, GSC-6","irrigations":3},
    "onion":    {"sow":"Oct–Nov","grow":"Nov–Feb","harvest":"Mar–Apr","duration":"110–130 days","seasons":["Rabi"],"bestVariety":"Agrifound White, Nasik Red, N-53","irrigations":12},
}

WATER_REQUIREMENTS = {
    "wheat":    {"sowing":5,"tillering":6,"jointing":7,"heading":6,"grain_fill":5,"total":550},
    "rice":     {"transplanting":8,"tillering":6,"panicle":7,"grain_fill":5,"total":1200},
    "cotton":   {"germination":4,"squaring":6,"boll_dev":8,"maturity":4,"total":700},
    "soybean":  {"germination":3,"flowering":5,"pod_fill":6,"maturity":3,"total":450},
    "sugarcane":{"germination":6,"tillering":8,"grand_growth":10,"maturity":5,"total":1800},
    "maize":    {"germination":4,"vegetative":6,"silking":8,"grain_fill":5,"total":500},
}

AGRI_NEWS = [
    {"title":"PM-KISAN 19th installment released — ₹2,000 credited to 9.4 crore farmers","time":"2 hours ago","category":"Policy","icon":"💰","summary":"The government has released the 19th installment of PM-KISAN scheme directly into farmers' bank accounts."},
    {"title":"Wheat MSP hiked to ₹2,425/quintal for 2025–26 Rabi season","time":"1 day ago","category":"Market","icon":"📈","summary":"Cabinet Committee on Economic Affairs approved the hike to support farmers' income and encourage production."},
    {"title":"New high-yield wheat variety 'Raj-4238' released for Central India","time":"2 days ago","category":"Technology","icon":"🌾","summary":"ICAR releases new variety with 15% higher yield potential and resistance to yellow rust disease."},
    {"title":"Locust warning issued for Rajasthan and Gujarat borders","time":"3 days ago","category":"Alert","icon":"⚠️","summary":"Desert locust swarms spotted near Pakistan border. Farmers advised to be alert and report sightings."},
    {"title":"e-NAM platform crosses ₹3 lakh crore in trade — record for agricultural markets","time":"4 days ago","category":"Market","icon":"🏆","summary":"National Agriculture Market platform achieves milestone, benefiting over 1.8 crore registered farmers."},
    {"title":"Drip irrigation subsidy increased to 60% for small farmers in 15 states","time":"5 days ago","category":"Scheme","icon":"💧","summary":"PM Krishi Sinchayee Yojana expanded with higher subsidy component for marginal farmers under 2 acres."},
]

SCHEMES = [
    {"name":"PM-KISAN","icon":"💰","benefit":"₹6,000/year direct transfer in 3 installments","eligibility":"All small & marginal farmers with cultivable land","link":"https://pmkisan.gov.in","color":"#2d6a4f"},
    {"name":"Fasal Bima Yojana","icon":"🛡️","benefit":"Crop insurance at subsidised 1.5–5% premium","eligibility":"Farmers growing notified crops in notified areas","link":"https://pmfby.gov.in","color":"#1e4d6b"},
    {"name":"Kisan Credit Card","icon":"💳","benefit":"Credit up to ₹3 lakh at 4% interest rate","eligibility":"All farmers, sharecroppers, tenant farmers","link":"https://www.nabard.org","color":"#4a1942"},
    {"name":"e-NAM Portal","icon":"📱","benefit":"Sell to pan-India buyers, 5–8% better prices","eligibility":"Farmers near registered mandis (1000+ mandis)","link":"https://enam.gov.in","color":"#7a3b00"},
    {"name":"Soil Health Card","icon":"🧪","benefit":"Free soil testing + nutrient recommendation","eligibility":"All farmers — apply at nearest soil testing lab","link":"https://soilhealth.dac.gov.in","color":"#4a3b00"},
    {"name":"PM Krishi Sinchayee","icon":"💧","benefit":"55–60% subsidy on drip/sprinkler installation","eligibility":"Farmers with min 0.5 acre landholding","link":"https://pmksy.gov.in","color":"#003d4d"},
]

DEMO_RESPONSES = {
    "en":{
        "yellow":"🌾 **Yellow Leaf Analysis for Wheat**\n\n**Most likely cause: Nitrogen Deficiency (85% probability)**\n\n**Immediate action:**\n• Apply 1 bag Urea (50kg) per acre immediately\n• Best time: Early morning (6–8 AM)\n• Method: Broadcast or band placement near roots\n\n**Secondary possibilities:**\n• Powdery Mildew — spray Mancozeb @ 2.5g/L if white powder visible\n• Waterlogging — check drainage if soil is wet\n• Sulfur deficiency — apply Gypsum @ 100kg/acre\n\n**For your Black soil in MP:** Split application recommended — half now, half after 15 days\n\n📅 Expected recovery: 7–10 days after urea application",
        "irrigat":"💧 **Irrigation Advisory — Precision Schedule**\n\n**Current crop stage analysis (Wheat, MP):**\n\n| Stage | Water Need | Next Due |\n|---|---|---|\n| Tillering | 6 cm/irrigation | 3–4 days |\n\n**Recommended schedule:**\n• **Frequency:** Every 12–14 days\n• **Amount:** 5–6 cm per irrigation\n• **Method:** Furrow irrigation (black soil)\n• **Time:** Early morning (reduces evaporation by 30%)\n\n**Total irrigations needed:** 5 (Crown Root, Tillering, Jointing, Flowering, Grain filling)\n\n⚠️ Weather alert: Low rainfall expected. Don't delay beyond 5 days.\n\n💡 Tip: Install soil moisture sensor at 15cm depth for precision irrigation",
        "fertil":"🌱 **Complete Fertilizer Schedule**\n\n**For Wheat on Black soil (2.5 acres, MP)**\n\n| Nutrient | Product | Total/acre | When |\n|---|---|---|---|\n| N | Urea | 50 kg | Split 3 doses |\n| P | DAP | 25 kg | Basal only |\n| K | MOP | 20 kg | Basal only |\n| S | Gypsum | 100 kg | Basal |\n| Zn | Zinc Sulphate | 5 kg | Basal |\n\n**Application schedule:**\n• **Basal (sowing):** Full DAP + MOP + Gypsum + Zinc + ⅓ Urea\n• **21 DAS (CRI stage):** ⅓ Urea\n• **42 DAS (Tillering):** ⅓ Urea\n\n💰 Estimated cost: ₹3,200/acre | Expected yield boost: 15–20%",
        "pest":"🐛 **Integrated Pest Management Guide**\n\n**Season-specific threats for Wheat in MP:**\n\n**🔴 High Alert:**\n• **Aphids (Maahu):** Spray Imidacloprid 17.8 SL @ 0.5ml/L\n• **Yellow Rust:** Propiconazole @ 1ml/L at first sign\n\n**🟡 Monitor:**\n• **Termites:** Chlorpyrifos in irrigation water\n• **Rodents:** Zinc phosphide bait @ 750g/ha\n\n**Prevention calendar:**\n• Week 1–4: Seed treatment with Carbendazim\n• Week 5–8: Scout weekly for aphids\n• Week 9–12: Watch for rust pustules\n\n⚠️ Don't spray within 15 days of harvest\n💡 Use sticky yellow traps to monitor pest pressure",
        "market":"📈 **Market Intelligence Report**\n\n**Wheat prices (Today):**\n• MSP: ₹2,275/quintal\n• Bhopal Mandi: ₹2,340 ↑ (+₹65 above MSP)\n• Indore Mandi: ₹2,310 ↑\n• Ujjain Mandi: ₹2,290 →\n\n**Price forecast (next 30 days):** 📈 Bullish\nPost-harvest demand expected to push prices 3–5% higher\n\n**Best selling strategy:**\n• Store for 3–4 weeks if you have proper storage\n• Target ₹2,400–2,450 range in April\n• Register on e-NAM for better buyer access\n\n💡 Quality tip: Moisture below 12% gets premium price",
        "season":"📅 **Complete Sowing Calendar (MP)**\n\n**Rabi Season (Oct–Mar):**\n| Crop | Sow | Harvest | Duration |\n|---|---|---|---|\n| Wheat | Oct 15–Nov 30 | Mar–Apr | 120–150 days |\n| Mustard | Oct 1–31 | Feb–Mar | 110–140 days |\n| Gram | Oct 15–Nov 15 | Feb–Mar | 90–110 days |\n\n**Kharif Season (Jun–Oct):**\n| Crop | Sow | Harvest | Duration |\n|---|---|---|---|\n| Soybean | Jun 15–Jul 15 | Oct | 90–110 days |\n| Rice | Jun 20–Jul 20 | Oct–Nov | 110–145 days |\n| Maize | Jun 15–Jul 10 | Sep–Oct | 85–95 days |\n\n🌱 **Current recommendation:** Late Rabi window closing. Consider HI-8498 short-duration wheat variety.",
        "default":"🌾 **Personalised Farm Advisory**\n\nBased on your profile (Wheat, Black soil, MP, 2.5 acres):\n\n**This week's priorities:**\n✅ Check soil moisture — irrigate if below 50% field capacity\n✅ Scout for aphids — 5 plants/metre check\n✅ Monitor weather — spray window open today\n\n**Quick stats for your farm:**\n• Expected yield: 18–22 quintals/acre\n• Estimated revenue: ₹42,000–51,000/acre\n• Next critical stage: Jointing (in ~2 weeks)\n\nAsk me anything specific — pest ID, fertilizer rates, or market timing!",
    },
    "hi":{
        "yellow":"🌾 **गेहूँ में पीले पत्तों का विश्लेषण**\n\n**सबसे संभावित कारण: नाइट्रोजन की कमी**\n\n**तुरंत करें:**\n• 1 बोरी यूरिया (50 किग्रा/एकड़) तुरंत डालें\n• सुबह 6–8 बजे डालना सबसे अच्छा\n• जड़ों के पास ड्रेसिंग विधि से डालें\n\n**अन्य संभावित कारण:**\n• पाउडरी मिल्ड्यू — सफेद पाउडर हो तो मैन्कोज़ेब @ 2.5 ग्राम/लीटर\n• जलभराव — मिट्टी गीली हो तो जल निकासी सुनिश्चित करें\n\n📅 7–10 दिन में सुधार दिखेगा",
        "irrigat":"💧 **सिंचाई सलाह**\n\n**आपकी फसल के लिए सटीक कार्यक्रम:**\n\n• हर **12–14 दिन** में सिंचाई करें\n• प्रत्येक बार 5–6 सेमी पानी दें\n• काली मिट्टी में फ़रो विधि सबसे उपयुक्त\n• सुबह सिंचाई करें — 30% पानी बचता है\n\n**कुल सिंचाई:** 5 बार (बुवाई से कटाई तक)\n\n⚠️ इस सप्ताह कम बारिश — 5 दिन से ज़्यादा देरी न करें",
        "fertil":"🌱 **पूर्ण उर्वरक कार्यक्रम**\n\n**गेहूँ, काली मिट्टी (2.5 एकड़):**\n\n• यूरिया: 50 किग्रा/एकड़ (3 भागों में)\n• DAP: 25 किग्रा/एकड़ (बुवाई पर)\n• MOP: 20 किग्रा/एकड़ (बुवाई पर)\n• जिप्सम: 100 किग्रा/एकड़\n• जिंक सल्फेट: 5 किग्रा/एकड़\n\n**अनुमानित लागत:** ₹3,200/एकड़\n**उपज वृद्धि:** 15–20% अधिक",
        "pest":"🐛 **एकीकृत कीट प्रबंधन**\n\n**इस मौसम में मुख्य कीट:**\n\n🔴 **तत्काल ध्यान:**\n• माहू — इमिडाक्लोप्रिड @ 0.5 मिली/लीटर\n• पीला रतुआ — प्रोपिकोनाज़ोल @ 1 मिली/लीटर\n\n🟡 **निगरानी करें:**\n• दीमक — सिंचाई में क्लोरपाइरीफॉस\n\n⚠️ कटाई से 15 दिन पहले कीटनाशक बंद करें",
        "market":"📈 **आज के बाज़ार भाव**\n\nMSP गेहूँ: ₹2,275/क्विंटल\n\n• भोपाल: ₹2,340 ↑ (MSP से ₹65 अधिक)\n• इंदौर: ₹2,310 ↑\n• उज्जैन: ₹2,290 →\n\n**अगले 30 दिन का अनुमान:** 📈 बढ़त संभव\n\n💡 सुझाव: 3–4 हफ्ते रोककर बेचें — ₹2,400+ मिल सकते हैं\ne-NAM पर पंजीकरण से 5–8% बेहतर भाव मिलेगा",
        "season":"📅 **बुवाई कैलेंडर (MP)**\n\n**रबी मौसम:**\n• गेहूँ: 15 अक्टूबर – 30 नवम्बर\n• सरसों: 1 – 31 अक्टूबर\n• चना: 15 अक्टूबर – 15 नवम्बर\n\n**खरीफ मौसम:**\n• सोयाबीन: 15 जून – 15 जुलाई\n• धान: 20 जून – 20 जुलाई\n• मक्का: 15 जून – 10 जुलाई\n\n🌱 अभी: देर रबी की खिड़की बंद हो रही है। HI-8498 किस्म आज़माएं।",
        "default":"🌾 **आपकी व्यक्तिगत कृषि सलाह**\n\nआपके खेत (गेहूँ, काली मिट्टी, MP, 2.5 एकड़) के लिए:\n\n**इस हफ्ते की प्राथमिकताएं:**\n✅ मिट्टी की नमी जांचें — ज़रूरत हो तो सिंचाई करें\n✅ माहू की जांच करें — 5 पौधे प्रति मीटर\n✅ मौसम अनुकूल है — आज छिड़काव कर सकते हैं\n\n**आपके खेत का अनुमान:**\n• उपज: 18–22 क्विंटल/एकड़\n• आय: ₹42,000–51,000/एकड़\n\nकोई भी सवाल पूछें — हम हिंदी में जवाब देंगे!",
    }
}

# ── Routes ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "ai_enabled": bool(OPENAI_API_KEY)})

@app.get("/api/weather/{state}")
async def get_weather(state: str):
    state = state.upper()
    demo = WEATHER_DATA.get(state, WEATHER_DATA["MP"])
    if WEATHER_API_KEY:
        cities = {"MP":"Bhopal","UP":"Lucknow","MH":"Pune","PB":"Amritsar","RJ":"Jaipur","GJ":"Ahmedabad","HR":"Chandigarh","AP":"Vijayawada"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get("https://api.openweathermap.org/data/2.5/weather",
                    params={"q":f"{cities.get(state,'Bhopal')},IN","appid":WEATHER_API_KEY,"units":"metric"})
                if r.status_code == 200:
                    d = r.json()
                    return {**demo, "temp":round(d["main"]["temp"]), "feels":round(d["main"]["feels_like"]),
                            "desc":d["weather"][0]["description"].title(), "humidity":d["main"]["humidity"],
                            "wind":round(d["wind"]["speed"]*3.6), "source":"live"}
        except: pass
    return {**demo, "source":"demo"}

@app.get("/api/market")
async def get_market():
    result = []
    for item in MARKET_DATA:
        fluctuation = random.randint(-20, 30)
        new_trend = item["trend"][1:] + [item["trend"][-1] + fluctuation]
        result.append({**item, "price": item["price"] + fluctuation,
                        "change": item["change"] + random.randint(-8, 8), "trend": new_trend})
    return {"prices": result, "updated": datetime.now().strftime("%d %b %Y %I:%M %p")}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if OPENAI_API_KEY:
        return await _ai_chat(req)
    m = req.message.lower()
    lang = req.language if req.language in DEMO_RESPONSES else "en"
    r = DEMO_RESPONSES[lang]
    if any(w in m for w in ["yellow","पीले","colour","color","leaves","पत्ते","pale"]): reply = r["yellow"]
    elif any(w in m for w in ["irrigat","water","सिंचाई","पानी","when to water"]): reply = r["irrigat"]
    elif any(w in m for w in ["fertil","urea","खाद","उर्वरक","dap","npk","manure"]): reply = r["fertil"]
    elif any(w in m for w in ["pest","insect","bug","कीट","कीड़","disease","रोग","spray"]): reply = r["pest"]
    elif any(w in m for w in ["price","market","sell","भाव","मंडी","rate","msp"]): reply = r["market"]
    elif any(w in m for w in ["sow","season","when","बुवाई","मौसम","calendar","plant"]): reply = r["season"]
    else: reply = r["default"]
    return {"reply": reply, "mode": "demo"}

async def _ai_chat(req: ChatRequest):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    w = WEATHER_DATA.get(req.state.upper(), WEATHER_DATA["MP"])
    lang_inst = "Reply entirely in Hindi (Devanagari script)." if req.language == "hi" else "Reply in clear English."
    system = f"""You are KisanAI, India's most advanced agricultural advisor.
Farmer: State={req.state}, Crop={req.crop}, Soil={req.soil}, Land={req.land}acres
Weather: {w['temp']}°C, {w['desc']}, Humidity={w['humidity']}%
{lang_inst} Be specific, practical, use tables where helpful. Use Indian context, emojis, bold headers. Max 250 words."""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},{"role":"user","content":req.message}],
            max_tokens=500, temperature=0.7)
        return {"reply": resp.choices[0].message.content, "mode": "ai"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pest-detect")
async def pest_detect(file: UploadFile = File(...), language: str = Form("en")):
    contents = await file.read()
    if not contents: raise HTTPException(400, "Empty file")
    if len(contents) > 10*1024*1024: raise HTTPException(400, "File too large. Max 10MB.")
    if OPENAI_API_KEY:
        return await _vision_detect(contents, file.content_type or "image/jpeg", language)
    return {**random.choice(PEST_DEMO), "mode": "demo"}

async def _vision_detect(image_bytes, content_type, language):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    b64 = base64.b64encode(image_bytes).decode()
    prompt = f"""Analyze this crop image as an Indian agricultural expert. {'Reply in Hindi.' if language=='hi' else 'Reply in English.'}
Respond ONLY with valid JSON: {{"name":"...","confidence":85,"description":"2 sentences","treatment":"2-3 sentences","severity":"None|Low|Medium|High","organic":"organic alternative treatment"}}"""
    try:
        resp = await client.chat.completions.create(model="gpt-4o",
            messages=[{"role":"user","content":[{"type":"image_url","image_url":{"url":f"data:{content_type};base64,{b64}","detail":"low"}},{"type":"text","text":prompt}]}],
            max_tokens=350)
        raw = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        return {**json.loads(raw), "mode":"ai"}
    except:
        return {**random.choice(PEST_DEMO), "mode":"demo"}

@app.post("/api/soil-advisory")
async def soil_advisory(req: SoilRequest):
    soil_profiles = {
        "black":    {"desc":"Vertisol — high clay content, excellent water retention, self-mulching.","ph_range":"7.5–8.5","om":"Medium","drainage":"Poor to moderate"},
        "red":      {"desc":"Porous, well-drained, low in N, P and organic matter.","ph_range":"6.0–7.0","om":"Low","drainage":"Good"},
        "alluvial": {"desc":"Highly fertile, ideal for intensive agriculture, good texture.","ph_range":"6.5–7.5","om":"Medium-High","drainage":"Moderate"},
        "sandy":    {"desc":"Low water retention, needs frequent irrigation and fertilization.","ph_range":"6.0–7.0","om":"Very Low","drainage":"Excellent"},
        "loamy":    {"desc":"Ideal balance of sand, silt and clay — best for most crops.","ph_range":"6.0–7.0","om":"High","drainage":"Good"},
    }
    npk = {"wheat":{"N":120,"P":60,"K":40},"rice":{"N":100,"P":50,"K":50},"cotton":{"N":160,"P":80,"K":80},"soybean":{"N":30,"P":60,"K":40},"sugarcane":{"N":250,"P":100,"K":120},"maize":{"N":120,"P":60,"K":40},"mustard":{"N":90,"P":40,"K":30},"onion":{"N":100,"P":50,"K":75}}.get(req.crop,{"N":100,"P":50,"K":40})
    ph_advice = f"pH {req.ph} is acidic. Apply 1–2 tonnes of lime per acre." if req.ph < 6.0 else f"pH {req.ph} is alkaline. Apply gypsum @ 250 kg/acre." if req.ph > 8.5 else f"pH {req.ph} is optimal ✅"
    soil = soil_profiles.get(req.soil, soil_profiles["loamy"])
    return {"soil_profile":soil,"npk":npk,"ph_advice":ph_advice,"organic":"Apply 5 tonnes FYM or 2 tonnes vermicompost per acre before sowing.","micro":"Zinc Sulphate @ 25 kg/ha + Borax @ 5 kg/ha once every 3 seasons.","score":random.randint(62,88)}

@app.post("/api/water-calculator")
async def water_calculator(req: WaterRequest):
    wr = WATER_REQUIREMENTS.get(req.crop, WATER_REQUIREMENTS["wheat"])
    stage_need = wr.get(req.stage, 6)
    soil_factor = {"black":0.85,"alluvial":0.90,"loamy":0.90,"red":1.10,"sandy":1.25}.get(req.soil,1.0)
    water_per_acre = round(stage_need * soil_factor, 1)
    total_water = round(water_per_acre * req.area, 1)
    return {"stage":req.stage,"water_per_acre":water_per_acre,"total_for_farm":total_water,"unit":"cm","duration_hrs":round(total_water*req.area/2,1),"next_irrigation_days":random.randint(10,16),"total_seasonal":wr["total"],"tip":f"Best time: Early morning 5–7 AM. Reduces evaporation by 35%."}

@app.get("/api/crop-calendar/{crop}")
async def crop_calendar(crop: str):
    cal = CROP_CALENDAR.get(crop.lower(), CROP_CALENDAR["wheat"])
    return cal

@app.get("/api/news")
async def get_news():
    return {"news": AGRI_NEWS, "updated": datetime.now().strftime("%d %b %Y")}

@app.get("/api/schemes")
async def get_schemes():
    return {"schemes": SCHEMES}

@app.get("/api/yield-estimate")
async def yield_estimate(crop: str = "wheat", soil: str = "black", land: float = 2.5, irrigation: int = 3):
    base = {"wheat":22,"rice":28,"cotton":15,"soybean":18,"maize":30,"mustard":12,"sugarcane":300,"onion":80}.get(crop,20)
    soil_m = {"black":1.0,"alluvial":1.1,"loamy":1.05,"red":0.9,"sandy":0.85}.get(soil,1.0)
    irr_m = min(1.0, 0.7 + irrigation * 0.06)
    yield_q = round(base * soil_m * irr_m, 1)
    price = next((m["price"] for m in MARKET_DATA if m["crop"].lower()==crop.lower()), 2300)
    return {"crop":crop,"yield_per_acre":yield_q,"total_yield":round(yield_q*land,1),"estimated_revenue":round(yield_q*land*price/100,0),"price_per_quintal":price}

@app.get("/health")
async def health():
    return {"status":"ok","version":"2.0","ai":bool(OPENAI_API_KEY),"mode":"AI Active" if OPENAI_API_KEY else "Demo Mode"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    print(f"\n🌾  KisanAI v2  →  http://localhost:{port}")
    print(f"   Mode: {'✅ AI Active (GPT-4)' if OPENAI_API_KEY else '⚡ Demo Mode'}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
