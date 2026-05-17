# Довідник API MyHaven

**Версія:** 1.1 | **Оновлено:** 15 травня 2026 р.

## Автентифікація
Більшість ендпоінтів API потребують дійсного JWT-токена.
- **Заголовок**: `Authorization: Bearer <token>`
- **Отримання токена**: `POST /api/token/`
- **Оновлення токена**: `POST /api/token/refresh/`

## Карта API

### 1. Користувачі та профілі (`/api/users/`)
- `POST register/`: Створення облікового запису.
- `GET me/`: Дані поточного автентифікованого користувача.
- `GET/PATCH profile/`: Управління профілем.
- `POST change-password/`: Оновлення пароля.
- `POST delete-account/`: Видалення облікового запису.
- `GET export-data/`: Експорт даних у форматі JSON.
- `GET totp/setup/`: Генерація QR-коду 2FA.
- `POST totp/verify/`: Верифікація 2FA.

### 2. Транзакції (`/transactions/api/`)
- `GET dashboard/`: Підсумок KPI.
- `GET statistics/`: Щомісячна агрегація даних.
- `GET list/`: Відфільтрований список транзакцій.
- `POST create/`: Ручне введення.
- `GET/PATCH/DELETE <id>/`: Управління записами.
- `GET categories/`: Список категорій.
- `GET calendar/`: Агреговані дані календаря.
- `POST uploads/`: Завантаження виписки (PDF/Excel).

### 3. Бюджети (`/api/budgets/`)
- `GET /`: Список бюджетів на поточний місяць.
- `POST /`: Створення бюджету.
- `GET/PATCH/DELETE <id>/`: Управління бюджетами.

### 4. Telegram API (`/api/telegram/`)
- `GET health/`: Перевірка з'єднання.
- `GET dashboard/`: Дані підсумку для бота.
- `GET transactions/`: Останні записи.
- `POST transactions/`: Швидке введення.
- `GET categories/`: Список категорій.

## Документація та схема
- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Схема OpenAPI**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Поширені коди статусів
- **200 OK**: Запит успішний.
- **201 Created**: Ресурс створено.
- **400 Bad Request**: Помилка валідації або синтаксису.
- **401 Unauthorized**: Потрібна автентифікація або вона недійсна.
- **403 Forbidden**: Доступ заборонено.
- **404 Not Found**: Ресурс не знайдено.
- **500 Server Error**: Помилка внутрішньої обробки.
