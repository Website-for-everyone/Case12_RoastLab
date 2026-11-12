"""
Roast Lab — SQLite Database Engine
Stores coffee bean inventory, flavor profiles, drip packs, and order records.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "roastlab.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for coffee beans inventory & flavor radar scores (1-10)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        origin TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        process TEXT NOT NULL,
        altitude TEXT NOT NULL,
        acidity INTEGER NOT NULL,
        sweetness INTEGER NOT NULL,
        bitterness INTEGER NOT NULL,
        body INTEGER NOT NULL,
        floral INTEGER NOT NULL,
        descriptors TEXT NOT NULL,
        roast_level TEXT NOT NULL,
        price_250g INTEGER NOT NULL,
        price_1kg INTEGER NOT NULL,
        in_stock BOOLEAN DEFAULT 1
    )
    """)
    
    # Table for drip packs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drip_packs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        box_count INTEGER NOT NULL,
        price_rub INTEGER NOT NULL,
        description TEXT NOT NULL
    )
    """)
    
    # Table for orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_identifier TEXT NOT NULL,
        client_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        order_type TEXT NOT NULL,
        pickup_time TEXT,
        items_json TEXT NOT NULL,
        total_amount_rub INTEGER NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )
    """)
    
    # Seed default beans if empty
    cursor.execute("SELECT COUNT(*) FROM beans")
    if cursor.fetchone()[0] == 0:
        default_beans = [
            ("Ethiopia Yirgacheffe Chelchele", "Ethiopia", "ethiopia_yirgacheffe", "Washed", "1950-2100m", 9, 8, 2, 5, 10, "Бергамот, белый жасмин, спелый персик, лемонграсс", "Light / Filter", 950, 3200, 1),
            ("Colombia Huila Supremo", "Colombia", "colombia_huila", "Washed", "1650-1800m", 6, 9, 4, 7, 6, "Красное яблоко, молочный шоколад, тростниковый сахар", "Medium / Omni", 880, 2900, 1),
            ("Kenya Nyeri AA Kirinyaga", "Kenya", "kenya_nyeri", "Washed", "1750-1900m", 10, 8, 3, 6, 8, "Черная смородина, спелый грейпфрут, брусничный джем", "Light / Filter", 1100, 3700, 1),
            ("Brazil Cerrado Dulce", "Brazil", "brazil_cerrado", "Natural", "1000-1150m", 3, 7, 6, 9, 3, "Жареный фундук, темный шоколад, карамельная помадка", "Medium-Dark / Espresso", 750, 2500, 1),
            ("Costa Rica Tarrazu Jaguar", "Costa Rica", "costa_rica_tarrazu", "Honey", "1500-1700m", 7, 9, 3, 7, 7, "Липовый мед, сушеный инжир, темная слива", "Medium / Filter", 980, 3300, 1),
            ("Rwanda Bourbon CWS", "Rwanda", "rwanda_bourbon", "Washed", "1800-2000m", 8, 8, 3, 6, 9, "Черный чай с бергамотом, цветы апельсина, клюква в сахаре", "Light / Filter", 920, 3100, 1),
        ]
        cursor.executemany("""
        INSERT INTO beans 
        (name, origin, slug, process, altitude, acidity, sweetness, bitterness, body, floral, descriptors, roast_level, price_250g, price_1kg, in_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_beans)

    # Seed default drip packs if empty
    cursor.execute("SELECT COUNT(*) FROM drip_packs")
    if cursor.fetchone()[0] == 0:
        default_drips = [
            ("Drip Box 'African Gems' (10 шт)", "drip_africa", 10, 990, "5х Эфиопия Иргачефф + 5х Кения Ньери для яркого утра"),
            ("Drip Box 'South America Comfort' (10 шт)", "drip_america", 10, 890, "5х Бразилия Серрадо + 5х Колумбия Уила с шоколадно-карамельным профилем"),
            ("Drip Box 'Geisha & Rare Micro-lots' (10 шт)", "drip_rare", 10, 1490, "Эксклюзивная подборка микролотов анаэробной ферментации")
        ]
        cursor.executemany("""
        INSERT INTO drip_packs (title, slug, box_count, price_rub, description)
        VALUES (?, ?, ?, ?, ?)
        """, default_drips)
        
    conn.commit()
    conn.close()

def get_all_beans() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beans WHERE in_stock = 1 ORDER BY price_250g ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_bean_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beans WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_drip_packs() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drip_packs ORDER BY price_rub ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_order(order_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO orders 
    (user_identifier, client_name, phone, order_type, pickup_time, items_json, total_amount_rub, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_data.get("user_identifier", "web_client"),
        order_data.get("client_name", "Anonymous"),
        order_data.get("phone", "N/A"),
        order_data.get("order_type", "delivery"),
        order_data.get("pickup_time", None),
        order_data.get("items_json", "[]"),
        order_data.get("total_amount_rub", 0),
        order_data.get("notes", "")
    ))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_last_user_order(user_identifier: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM orders 
    WHERE user_identifier = ? 
    ORDER BY created_at DESC 
    LIMIT 1
    """, (user_identifier,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Initialize on import
init_db()
