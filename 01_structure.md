# АРХИТЕКТУРА И СПЕЦИФИКАЦИЯ ПРОЕКТА: ROAST LAB

> **Проект:** Roast Lab — Спешелти-ростерия и крафтовая кофейня  
> **Клиент / Заказчик:** Roast Lab Coffee Roasters (Москва / Санкт-Петербург)  
> **Чек проекта:** 320,000 ₽ | **Срок:** 14 дней (Дедлайн: 2026-11-25)  
> **Дедлайн MVP (80%):** 2026-11-22  
> **Тип договора:** Договор СМЗ с ИП (Чек «Мой Налог»)

---

## 🛠 Технологический стек
- **Frontend / UI:** HTML5 / CSS3 / JavaScript (Vanilla SPA), Craft Specialty Coffee Aesthetic, Dynamic SVG Flavor Radar Engine, Craft Paper Texture Overlays
- **Backend & Logic:** Python 3.12, FastAPI, Uvicorn, SQLite3, Pydantic v2
- **Telegram Bot:** Aiogram 3.x (Asyncio, FSM, Multi-category Storefront, Pre-order Pickup Scheduler, 1-Click Reorder)
- **Уведомления и лиды:** Автоматическая отправка структурированных заказов в @Idrisov_prod

---

## 🏛 Архитектурная схема
```
[ Гость на сайте ] ──► [ Радар вкуса & 3-шаговый Квиз ] ──► [ REST API /api/orders ] ────┐
                                                                                         ▼
[ Гость в Telegram ] ──► [ Roast Lab Bot (Зерно / Дрипы / Предзаказ) ] ──────────► [ SQLite DB ]
                                                                                         │
                                                                                         ▼
                                                                             [ Бариста & @Idrisov_prod ]
```

---

## 🔐 Переменные окружения (.env.example)
```env
BOT_TOKEN=8217851677:AAHN34TMuC1P4e6SppuazFN8BIiLHa_RyIc
TELEGRAM_OWNER_ID=1387913438
TELEGRAM_OWNER_USERNAME=@Idrisov_prod
PORT=3012
API_PORT=8012
PROXY_URL=socks5://dsZwtR:PTJNnz@72.57.96.136:8000
DATABASE_PATH=roastlab.db
```

---

## 🔗 Ресурсы и ссылки
- **Порт Web UI / API:** `http://localhost:3012` / `http://localhost:8012`
- **Telegram Bot:** `@RoastLabCoffeeBot`
- **Канал заказов:** `@Idrisov_prod`
