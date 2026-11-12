"""
Roast Lab — FastAPI Backend
Provides flavor radar calculations, bean recommendation quiz, and order management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import math
import json
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

app = FastAPI(title="Roast Lab Specialty Coffee API", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

AXIS_ANGLES = [ -90, -18, 54, 126, 198 ] # 5 axes in degrees

def compute_radar_svg_points(acidity: int, sweetness: int, bitterness: int, body: int, floral: int,
                             center_x: float = 150.0, center_y: float = 150.0, max_radius: float = 110.0) -> str:
    """Computes SVG polygon points 'x1,y1 x2,y2 ...' from 5 attributes scaled 1 to 10."""
    values = [acidity, sweetness, bitterness, body, floral]
    points = []
    
    for val, angle_deg in zip(values, AXIS_ANGLES):
        ratio = max(0.1, min(1.0, val / 10.0))
        r = max_radius * ratio
        rad = math.radians(angle_deg)
        x = center_x + r * math.cos(rad)
        y = center_y + r * math.sin(rad)
        points.append(f"{round(x, 1)},{round(y, 1)}")
        
    return " ".join(points)

def get_recommended_recipe(brew_method: str, bean: Dict[str, Any]) -> Dict[str, str]:
    method = brew_method.lower()
    if "v60" in method or "filter" in method:
        return {
            "method_name": "Hario V60 / Воронка",
            "grind_size": "Средний (22-24 клика Comandante)",
            "water_temp": "93°C (фильтрованная вода 60-80 ppm)",
            "ratio": "1:16 (15г кофе на 240г воды)",
            "time": "2 мин 40 сек",
            "technique": "Предсмачивание 45г (40 сек), затем 2 плавных круговых вливания по 100г."
        }
    elif "espresso" in method:
        return {
            "method_name": "Эспрессо (9 бар)",
            "grind_size": "Тонкий эспрессо (8-10 кликов Comandante)",
            "water_temp": "92.5°C",
            "ratio": "1:2 (18г кофе -> 36г напитка)",
            "time": "26–28 сек",
            "technique": "Равномерная темперация 15 кг, плавная предэкстракция 4 сек."
        }
    elif "cold" in method:
        return {
            "method_name": "Cold Brew / Холодный настой",
            "grind_size": "Крупный (32 клика)",
            "water_temp": "Комнатная вода (20°C)",
            "ratio": "1:8 (100г кофе на 800г воды)",
            "time": "14-16 часов в холодильнике",
            "technique": "Двойная фильтрация через бумажный фильтр, подача со льдом."
        }
    elif "french" in method or "press" in method:
        return {
            "method_name": "Френч-пресс",
            "grind_size": "Крупный равномерный (28 кликов)",
            "water_temp": "94°C",
            "ratio": "1:15 (20г кофе на 300г воды)",
            "time": "4 минуты",
            "technique": "Залить весь объем, перемешать корку на 4-й минуте, снять пену и опустить поршень."
        }
    else: # Milk drink
        return {
            "method_name": "Флэт Уайт / Капучино",
            "grind_size": "Тонкий эспрессо",
            "water_temp": "93°C",
            "ratio": "Двойной эспрессо (38г) + 140г взбитого молока",
            "time": "27 сек экстракция",
            "technique": "Глянцевая микропена 60°C, латте-арт тюльпан."
        }

def match_bean_quiz(brew_method: str, flavor_pref: str, milk_pref: str) -> Dict[str, Any]:
    beans = database.get_all_beans()
    
    # Priority matching
    if milk_pref in ["cream", "latte", "heavy"] or brew_method == "espresso":
        # Needs high sweetness and high body
        best_bean = next((b for b in beans if b["slug"] == "brazil_cerrado"), beans[0])
    elif flavor_pref in ["fruity", "berry"]:
        best_bean = next((b for b in beans if b["slug"] == "kenya_nyeri"), beans[0])
    elif flavor_pref in ["floral", "tea"]:
        best_bean = next((b for b in beans if b["slug"] == "ethiopia_yirgacheffe"), beans[0])
    elif flavor_pref in ["sweet_chocolate", "caramel"]:
        best_bean = next((b for b in beans if b["slug"] == "colombia_huila"), beans[0])
    elif flavor_pref in ["honey_fig"]:
        best_bean = next((b for b in beans if b["slug"] == "costa_rica_tarrazu"), beans[0])
    else:
        # Default balanced
        best_bean = next((b for b in beans if b["slug"] == "colombia_huila"), beans[0])
        
    recipe = get_recommended_recipe(brew_method, best_bean)
    radar_points = compute_radar_svg_points(
        best_bean["acidity"], best_bean["sweetness"], best_bean["bitterness"],
        best_bean["body"], best_bean["floral"]
    )
    
    return {
        "recommended_bean": best_bean,
        "radar_points": radar_points,
        "recipe": recipe
    }

# Pydantic Schemas
class QuizRequest(BaseModel):
    brew_method: str = "v60"
    flavor_preference: str = "fruity"
    milk_preference: str = "black"

class OrderItem(BaseModel):
    title: str
    variant: str = "250g"
    quantity: int = 1
    price_rub: int

class OrderRequest(BaseModel):
    client_name: str
    phone: str
    order_type: str = "delivery" # delivery or pickup
    pickup_time: Optional[str] = None
    items: List[OrderItem]
    notes: Optional[str] = ""
    user_identifier: Optional[str] = "web_user"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Roast Lab Specialty Coffee Backend</h1>")

@app.get("/api/beans")
async def api_get_beans():
    beans = database.get_all_beans()
    # Enrich with computed radar svg points
    for b in beans:
        b["radar_points"] = compute_radar_svg_points(
            b["acidity"], b["sweetness"], b["bitterness"], b["body"], b["floral"]
        )
    return {"status": "ok", "beans": beans}

@app.get("/api/drips")
async def api_get_drips():
    drips = database.get_all_drip_packs()
    return {"status": "ok", "drip_packs": drips}

@app.post("/api/quiz/recommend")
async def api_quiz_recommend(req: QuizRequest):
    result = match_bean_quiz(req.brew_method, req.flavor_preference, req.milk_preference)
    return {"status": "ok", **result}

@app.post("/api/orders")
async def api_create_order(req: OrderRequest):
    if not req.client_name.strip() or not req.phone.strip():
        raise HTTPException(status_code=422, detail="Укажите имя и телефон для оформления заказа")
    if not req.items:
        raise HTTPException(status_code=400, detail="Корзина пуста")
        
    total_amount = sum(item.price_rub * item.quantity for item in req.items)
    items_serialized = json.dumps([item.model_dump() for item in req.items], ensure_ascii=False)
    
    order_data = {
        "user_identifier": req.user_identifier or req.phone,
        "client_name": req.client_name,
        "phone": req.phone,
        "order_type": req.order_type,
        "pickup_time": req.pickup_time,
        "items_json": items_serialized,
        "total_amount_rub": total_amount,
        "notes": req.notes
    }
    order_id = database.create_order(order_data)
    
    lead_payload = {
        "project_name": "RoastLab",
        "lead_type": "coffee_order",
        "client_data": {
            "name": req.client_name,
            "phone": req.phone,
            "order_type": req.order_type,
            "pickup_time": req.pickup_time,
            "items_count": len(req.items),
            "total_rub": total_amount
        },
        "target_recipient": "@Idrisov_prod",
        "order_id": order_id
    }
    
    return {
        "status": "ok",
        "order_id": order_id,
        "total_amount_rub": total_amount,
        "lead_payload": lead_payload,
        "message": f"Заказ #{order_id} успешно оформлен! Бариста уже готовит ваш кофе."
    }

@app.get("/api/reorder/{user_identifier}")
async def api_reorder(user_identifier: str):
    last_order = database.get_last_user_order(user_identifier)
    if not last_order:
        raise HTTPException(status_code=404, detail="Предыдущие заказы не найдены")
    return {"status": "ok", "last_order": last_order}
