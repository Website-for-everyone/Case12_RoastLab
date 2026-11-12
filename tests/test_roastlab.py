"""
Unit and Smoke Tests for Case 12: Roast Lab
Verifies radar math, bean quiz matching, database CRUD, FastAPI endpoints, and bot handler registration.
"""

import pytest
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from backend.app import app, compute_radar_svg_points, match_bean_quiz, get_recommended_recipe
import database
from bot.bot import router, create_bot_and_dispatcher, is_cafe_open
from fastapi.testclient import TestClient

client = TestClient(app)

def test_radar_svg_points():
    points_str = compute_radar_svg_points(acidity=9, sweetness=8, bitterness=2, body=5, floral=10)
    coords = points_str.split(" ")
    assert len(coords) == 5
    for c in coords:
        x_str, y_str = c.split(",")
        x, y = float(x_str), float(y_str)
        # Verify within 0 to 300 canvas
        assert 0 <= x <= 300
        assert 0 <= y <= 300

def test_quiz_recommendation_fruity():
    result = match_bean_quiz(brew_method="v60", flavor_pref="fruity", milk_pref="black")
    bean = result["recommended_bean"]
    recipe = result["recipe"]
    assert "Kenya" in bean["name"] or "Ethiopia" in bean["name"]
    assert "V60" in recipe["method_name"]
    assert "grind_size" in recipe
    assert "water_temp" in recipe

def test_quiz_recommendation_milk():
    result = match_bean_quiz(brew_method="espresso", flavor_pref="sweet_chocolate", milk_pref="cream")
    bean = result["recommended_bean"]
    recipe = result["recipe"]
    assert "Brazil" in bean["name"] or "Colombia" in bean["name"]
    assert recipe["ratio"] is not None

def test_database_beans():
    beans = database.get_all_beans()
    assert len(beans) >= 5
    drips = database.get_all_drip_packs()
    assert len(drips) >= 2

def test_database_orders_and_reorder():
    order_data = {
        "user_identifier": "test_user_42",
        "client_name": "Daniel",
        "phone": "+79991234567",
        "order_type": "delivery",
        "items_json": '[{"title": "Ethiopia 250g", "price_rub": 950, "quantity": 1}]',
        "total_amount_rub": 950,
        "notes": "Fast roast"
    }
    order_id = database.create_order(order_data)
    assert order_id > 0

    last_order = database.get_last_user_order("test_user_42")
    assert last_order is not None
    assert last_order["client_name"] == "Daniel"
    assert last_order["total_amount_rub"] == 950

def test_api_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Roast Lab" in response.text

def test_api_beans_endpoint():
    response = client.get("/api/beans")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["beans"]) >= 5
    assert "radar_points" in data["beans"][0]

def test_api_drips_endpoint():
    response = client.get("/api/drips")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["drip_packs"]) >= 2

def test_api_quiz_endpoint():
    payload = {"brew_method": "v60", "flavor_preference": "floral", "milk_preference": "black"}
    response = client.post("/api/quiz/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_bean" in data
    assert "recipe" in data

def test_api_orders_validation():
    # Empty client name fails
    res_bad = client.post("/api/orders", json={"client_name": "", "phone": "", "items": []})
    assert res_bad.status_code == 422

    # Valid order
    payload = {
        "client_name": "Elena",
        "phone": "+79998887766",
        "order_type": "pickup",
        "pickup_time": "через 15 мин",
        "items": [{"title": "Kenya Nyeri", "variant": "250g", "quantity": 1, "price_rub": 1100}]
    }
    res_good = client.post("/api/orders", json=payload)
    assert res_good.status_code == 200
    data = res_good.json()
    assert data["status"] == "ok"
    assert data["order_id"] > 0
    assert data["total_amount_rub"] == 1100

def test_bot_registration():
    bot, dp = create_bot_and_dispatcher()
    assert bot is not None
    assert dp is not None
    assert len(router.message.handlers) >= 1
    assert len(router.callback_query.handlers) >= 6
