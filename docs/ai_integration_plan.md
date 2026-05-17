# 🧠 Інтеграція ШІ до MyHaven — Голосовий Telegram-бот

> **Мета:** Дозволити користувачу надсилати голосові повідомлення в Telegram, а бот — розпізнавати мову, розуміти намір і виконувати відповідний API-виклик (транзакції, бюджети тощо).

---

## Як це буде працювати (загальна схема)

```
[Голосове повідомлення] 
      ↓
[STT: Whisper — текст]
      ↓
[LLM: розуміє намір + витягує дані]
      ↓
[Маппінг на API MyHaven]
      ↓
[Відповідь користувачу в Telegram]
```

**Приклад:**
> 🎤 «Додай витрату 250 гривень на їжу вчора»
> 🤖 → `POST /api/telegram/transactions/` `{amount: -250, category: "Їжа", date: "2026-05-15"}`
> ✅ «Транзакцію додано: -250 грн, Їжа, 15 травня»

---

## 🔀 Варіант 1: Локальна модель через Ollama

### Що потрібно:
- **STT (розпізнавання мови):** `openai/whisper` локально (Python пакет `openai-whisper`)
- **LLM (розуміння намірів):** Ollama + одна з моделей (Mistral, LLaMA 3, Phi-3)
- **Запуск:** Ollama-сервер на тому ж комп'ютері, що і бекенд

### Мінімальні вимоги до моделі (параметри)

| Модель | Параметри | Вимоги до RAM | Якість NLU |
|--------|-----------|--------------|------------|
| Phi-3 Mini | **3.8B** | ~4 GB RAM | Достатньо для структурованих команд |
| Mistral 7B | **7B** | ~8 GB RAM | Добре, розуміє контекст |
| LLaMA 3 8B | **8B** | ~10 GB RAM | ✅ Рекомендовано |
| LLaMA 3 70B | 70B | ~48 GB RAM | Надлишково |

> **Відповідь на твоє питання:** Мінімум — **3.8B параметрів** (Phi-3 Mini). Але для впевненого розуміння украïнської мови та фінансового контексту — рекомендую **7B–8B** (Mistral 7B або LLaMA 3 8B).
> 
> ⚠️ Зверни увагу: "нейрозв'язки" і "параметри" — не одне й те саме, але в контексті трансформерів параметри — це аналог синаптичних ваг. Для цієї задачі 7B параметрів = ~7 мільярдів "нейрозв'язків".

### ✅ Плюси локальної моделі

| # | Перевага | Деталь |
|---|----------|--------|
| 1 | **Повна приватність** | Жодні фінансові дані не покидають твій сервер |
| 2 | **Нульова вартість API** | Немає плати за токени, немає rate limits |
| 3 | **Офлайн-робота** | Працює без Інтернету |
| 4 | **Повний контроль** | Можна fine-tune модель на своїх даних |
| 5 | **Без vendor lock-in** | Не залежиш від Google/OpenAI/Anthropic |

### ❌ Мінуси локальної моделі

| # | Недолік | Деталь |
|---|---------|--------|
| 1 | **Висока вимога до заліза** | 7B модель потребує ≥8 GB RAM (бажано GPU) |
| 2 | **Повільна швидкість без GPU** | На CPU відповідь 10–60 сек для 7B |
| 3 | **Слабка українська** | Більшість open-source моделей погано знають українську |
| 4 | **Складне налаштування** | Потрібен промпт-інжиніринг, тестування, підтримка |
| 5 | **Обслуговування** | Оновлення моделей, стабільність сервера — твоя відповідальність |

---

## 🌐 Варіант 2: Cloud API (Gemini Flash / OpenAI GPT-4o-mini)

### Що потрібно:
- **STT:** Telegram Voice → `Whisper API` (OpenAI) або `Google Speech-to-Text`
- **LLM:** `gemini-2.0-flash` або `gpt-4o-mini` — один API-виклик
- **Ключ:** `GEMINI_API_KEY` або `OPENAI_API_KEY` у `.env`

### ✅ Плюси Cloud API

| # | Перевага | Деталь |
|---|----------|--------|
| 1 | **Чудова якість** | Gemini Flash і GPT-4o-mini розуміють природну мову, в т.ч. українську |
| 2 | **Швидкість** | Відповідь за 0.5–2 секунди |
| 3 | **Легке налаштування** | pip install google-generativeai → 20 рядків коду |
| 4 | **Без вимог до заліза** | Працює на будь-якому сервері з Інтернетом |
| 5 | **Мультимодальність** | Gemini може напряму обробляти аудіо без окремого STT |
| 6 | **Free tier** | Gemini Flash має безкоштовний рівень (60 req/min) |

### ❌ Мінуси Cloud API

| # | Недолік | Деталь |
|---|---------|--------|
| 1 | **Приватність** | Фінансові дані надсилаються на сервери Google/OpenAI |
| 2 | **Вартість при масштабі** | При великому навантаженні — платно |
| 3 | **Залежність від Інтернету** | Без мережі — не працює |
| 4 | **Rate limits** | Free tier обмежений; при перевищенні — затримки |
| 5 | **Vendor lock-in** | Зміна цін або API = переробка коду |

---

## 🏆 Рекомендація

> **Для особистого проекту (MyHaven) — однозначно Gemini Flash API.**
>
> Причини: це персональний фінансовий застосунок (мало користувачів), швидкість важлива, в тебе вже є Django-бекенд і Telegram-бот — додати Gemini це буквально 50 рядків коду. Gemini Flash має безкоштовний tier достатній для особистого використання.
>
> Ollama — якщо хочеш навчитись або якщо з часом плануєш SaaS з тисячами користувачів і вимоги до приватності.

---

## 📋 Покроковий план реалізації (Gemini API — рекомендований шлях)

### Крок 1 — Отримати API ключ і встановити залежності

```bash
# У директорії telegrambot/
pip install google-generativeai openai-whisper
# або лише для STT через OpenAI Whisper API:
pip install openai
```

1. Зайти на [aistudio.google.com](https://aistudio.google.com) → отримати `GEMINI_API_KEY`
2. Додати в `telegrambot/.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```

---

### Крок 2 — Модуль `ai_processor.py` (новий файл у `telegrambot/`)

Цей модуль відповідає за:
- Транскрибацію голосу → текст (Whisper)
- Розуміння тексту → структурований намір (Gemini)

```python
# telegrambot/ai_processor.py

import json
import tempfile
import os
import google.generativeai as genai
import whisper

SYSTEM_PROMPT = """
Ти — асистент фінансового застосунку MyHaven. 
Твоє завдання: проаналізувати команду користувача і повернути JSON з наміром.

Можливі дії (action):
- create_transaction: {amount, category_name, description, date (YYYY-MM-DD)}
- get_transactions: {filters: {category, date_from, date_to}}
- get_dashboard: {}
- create_budget: {category_name, limit, month (YYYY-MM-01)}
- get_budgets: {month (optional)}
- delete_transaction: {id}
- update_transaction: {id, fields: {...}}
- unknown: {message: "пояснення що незрозуміло"}

Важливо:
- amount завжди число (витрати — від'ємні: -250, доходи — додатні: 1000)
- date: якщо "сьогодні" → поточна дата, "вчора" → вчорашня
- Відповідай ЛИШЕ JSON без markdown або пояснень

Приклад входу: "Додай витрату 250 гривень на їжу вчора"
Приклад виходу: {"action": "create_transaction", "amount": -250, "category_name": "Їжа", "description": "", "date": "2026-05-15"}
"""

class AIProcessor:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")
        self._whisper = whisper.load_model("base")  # або "small" для кращої точності

    async def transcribe_voice(self, ogg_path: str) -> str:
        """Транскрибує голосове повідомлення у текст."""
        result = self._whisper.transcribe(ogg_path, language="uk")
        return result["text"].strip()

    async def parse_intent(self, text: str, today: str) -> dict:
        """Розуміє намір із тексту та повертає структурований dict."""
        prompt = f"Сьогодні: {today}\nКоманда: {text}"
        response = self._model.generate_content(
            [SYSTEM_PROMPT, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
```

---

### Крок 3 — Обробник голосових повідомлень у `handlers.py`

Додати новий метод до класу `BotServices`:

```python
async def voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє голосові повідомлення через ШІ."""
    if not update.message or not update.message.voice or not update.effective_user:
        return

    # 1. Перевірити що акаунт прив'язаний
    link = self._require_link(update)
    if not link:
        await self._reply_text(update, "⚠️ Спочатку прив'яжи акаунт через /link")
        return

    await self._reply_text(update, "🎤 Обробляю голосове повідомлення...")

    # 2. Завантажити голосовий файл
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await voice_file.download_to_drive(tmp.name)
        ogg_path = tmp.name

    try:
        # 3. Транскрибувати
        text = await self._ai.transcribe_voice(ogg_path)
        await self._reply_text(update, f"🗣 Розпізнано: «{text}»")

        # 4. Розібрати намір
        today = datetime.date.today().isoformat()
        intent = await self._ai.parse_intent(text, today)

        # 5. Виконати відповідну дію
        await self._dispatch_intent(update, intent)

    finally:
        os.unlink(ogg_path)

async def _dispatch_intent(self, update: Update, intent: dict) -> None:
    """Маппінг наміру ШІ → API-виклик."""
    action = intent.get("action", "unknown")

    if action == "create_transaction":
        payload = {
            "amount": intent["amount"],
            "category_name": intent.get("category_name", ""),
            "description": intent.get("description", ""),
            "date": intent.get("date", datetime.date.today().isoformat()),
        }
        result = await self._call_api(update, "POST", build_telegram_path("transactions"), json=payload)
        await self._reply_result(update, result)

    elif action == "get_dashboard":
        result = await self._call_api(update, "GET", build_telegram_path("dashboard"))
        await self._reply_result(update, result)

    elif action == "get_transactions":
        filters = intent.get("filters", {})
        result = await self._call_api(update, "GET", build_telegram_path("transactions"), params=filters)
        await self._reply_result(update, result)

    elif action == "create_budget":
        payload = {
            "category_name": intent.get("category_name"),
            "limit": intent.get("limit"),
            "month": intent.get("month"),
        }
        result = await self._call_api(update, "POST", build_telegram_path("budgets"), json=payload)
        await self._reply_result(update, result)

    elif action == "get_budgets":
        params = {}
        if "month" in intent:
            params["month"] = intent["month"]
        result = await self._call_api(update, "GET", build_telegram_path("budgets"), params=params or None)
        await self._reply_result(update, result)

    elif action == "unknown":
        msg = intent.get("message", "Не вдалось розпізнати команду")
        await self._reply_text(update, f"❓ {msg}")

    else:
        await self._reply_text(update, f"⚠️ Невідома дія: {action}")
```

---

### Крок 4 — Реєстрація хендлера у `register_handlers()`

```python
# У кінці функції register_handlers():
from telegram.ext import MessageHandler, filters

application.add_handler(
    MessageHandler(filters.VOICE, services.voice_message)
)
```

---

### Крок 5 — Оновити `BotServices.__init__()` та `bot_config.py`

```python
# bot_config.py — додати поле:
gemini_api_key: str = ""

# handlers.py — у __init__:
from .ai_processor import AIProcessor

self._ai = AIProcessor(config.gemini_api_key)
```

---

### Крок 6 — Оновити `requirements.txt`

```
google-generativeai>=0.8.0
openai-whisper>=20240930
```

---

### Крок 7 — Тестування

| Тест | Голосова команда | Очікуваний результат |
|------|-----------------|---------------------|
| ✅ Створення транзакції | «Витратив 150 грн на таксі сьогодні» | POST /transactions/ з amount=-150 |
| ✅ Перегляд дешборду | «Покажи мій баланс» | GET /dashboard/ |
| ✅ Створення бюджету | «Встанови бюджет на їжу 3000 грн цього місяця» | POST /budgets/ |
| ✅ Список транзакцій | «Що я витрачав вчора?» | GET /transactions/ з фільтром |
| ✅ Незрозуміла команда | «Привіт як справи» | Повідомлення "не вдалось розпізнати" |

---

## Альтернативний план (Ollama — локальна модель)

### Додаткові кроки порівняно з Gemini:

**Крок 1-Ollama:** Встановити Ollama
```bash
# Завантажити з https://ollama.ai
ollama pull llama3.1:8b   # або mistral:7b
ollama serve              # запустити сервер на localhost:11434
```

**Крок 2-Ollama:** STT — встановити Whisper локально
```bash
pip install openai-whisper
# Завантажить модель автоматично (~150MB для "base", ~1GB для "medium")
```

**Крок 3-Ollama:** Змінити `ai_processor.py`:
```python
import httpx

class AIProcessor:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self._ollama_url = ollama_url
        self._whisper = whisper.load_model("small")

    async def parse_intent(self, text: str, today: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._ollama_url}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": f"{SYSTEM_PROMPT}\n\nСьогодні: {today}\nКоманда: {text}",
                    "format": "json",
                    "stream": False
                }
            )
        return json.loads(response.json()["response"])
```

---

## Підсумкове порівняння

| Критерій | Ollama (локально) | Gemini Flash API |
|----------|-------------------|-----------------|
| Вартість | 💚 Безкоштовно | 💛 Безкоштовно до ліміту |
| Швидкість | 🔴 10–60 сек (без GPU) | 💚 0.5–2 сек |
| Приватність | 💚 Повна | 🔴 Дані на серверах Google |
| Якість (укр.) | 🟡 Задовільна | 💚 Відмінна |
| Складність | 🔴 Висока | 💚 Низька |
| Залізо | 🔴 ≥8 GB RAM | 💚 Будь-який сервер |
| **Вердикт** | Для навчання/SaaS | **✅ Для особистого проекту** |
