# Regression Testing Guide — MyHaven Backend

**Version:** 1.0 | **Updated:** May 6, 2026

---

## 📌 Що таке Regression Testing?

**Регресійне тестування** — це перехопи всіх попередніх функцій після додання нової. Цель:
- Впевнитися, що новий код не "сломав" старий функціонал
- Знайти неочікувані побічні ефекти
- Захиститися від багів

### Просто: "Після мого коміту ВСІ тести повинні бути зеленими"

---

## ✅ Коли запускати Regression Tests?

| Коли | Команда |
|------|---------|
| Перед коммітом | `./run_checks.ps1` (Windows) або `./run_checks.sh` (Unix) |
| При розробці | `pytest -v` (показати всі тести) |
| Перед merge до main | CI/CD pipeline (GitHub Actions, etc.) |
| Щоденно (optional) | `pytest --cov=backend` (з покриттям) |

---

## 🚀 Команди для регресійного тестування

### 1. Запустити ВСІ тести в проекті

```bash
cd backend
pytest -v
```

**Вихід:**
```
tests/test_backend_cl.py::BackendCLUnitTests::test_database_connection PASSED
tests/test_backend_cl.py::BackendCLUnitTests::test_successful_statement_upload_processing PASSED
users/tests.py::UserServicesTests::test_export_service_contains_expected_sections PASSED
users/tests.py::UserServicesTests::test_account_deletion_service_removes_user_data PASSED
telegram_api/tests.py::TelegramApiTests::test_health_endpoint PASSED
telegram_api/tests.py::TelegramApiTests::test_transaction_create_and_list PASSED
... [more tests]

========================== 25 passed in 2.34s ==========================
```

### 2. Запустити тести з покриттям кода

```bash
pytest --cov=backend --cov-report=html
```

**Генерує:** `htmlcov/index.html` (відкрити в браузері для деталей)

### 3. Запустити тільки конкретного app

```bash
pytest users/ -v              # Тільки users
pytest telegram_api/ -v       # Тільки telegram_api
pytest tests/ -v              # Тільки integration tests
```

### 4. Запустити тест за ключовим словом

```bash
pytest -k "export" -v         # Тільки тести з "export" у назві
pytest -k "telegram" -v       # Тільки тести з "telegram" у назві
```

### 5. Запустити з вивідом помилок

```bash
pytest -v --tb=long          # Детальний стек помилок
pytest -v --tb=short         # Коротка версія
```

---

## 🎯 Сценарій регресійного тестування

### Сценарій 1: Ти додав новий endpoint у telegram_api

```bash
# 1. Запусти нові тести
pytest telegram_api/tests.py -v

# 2. Перевір, що старі тести ще проходять
pytest users/tests.py transactions/tests.py -v

# 3. Запусти ВСІ тести разом
pytest -v

# Якщо ВСІ зелені → можеш коммітити!
```

### Сценарій 2: Ти змінив serializer у users

```bash
# 1. Запусти тести users
pytest users/tests.py -v

# 2. Запусти тести, які можуть імпортувати users serializers
pytest telegram_api/tests.py -v

# 3. Повний набір
pytest -v
```

---

## 🚨 Коли регресійний тест падає?

### Приклад: Падіння тесту

```bash
$ pytest -v

...
users/tests.py::UserServicesTests::test_export_service_contains_expected_sections FAILED

=============== FAILURES ===============
AssertionError: 'telegram_user_id' in payload['profile']
```

### Дії:
1. **Прочитай помилку** — "telegram_user_id знайдена у profile"
2. **Знайди причину** — можливо, ти додав поле у `PrivateProfileSerializer`
3. **Виправи код** — видали поле або онови тест (якщо це було навмисно)
4. **Запусти тест знову** — `pytest users/tests.py::UserServicesTests::test_export_service_contains_expected_sections -v`
5. **Перевір регресію** — `pytest -v` (усі тести)

---

## 📊 Інтерпретація результатів

### ✅ Ідеальний результат

```
========================== 25 passed in 2.34s ==========================

Coverage: 82% (goal: >80%)
```

**Це означає:**
- Всі тести проходять
- 82% коду покритого тестами
- Можеш безпечно коммітити

### ⚠️ Попередження

```
========================== 24 passed, 1 skipped in 2.45s ==========================
```

**Це означає:**
- 1 тест пропущений (можливо, помічена функція як TODO)
- Решта проходять ✓

### ❌ Критична помилка

```
======================= 3 failed, 22 passed in 3.12s ==========================

FAILED tests/test_backend_cl.py::BackendCLUnitTests::test_kpi_aggregation_with_user_isolation
```

**Дії:**
1. Не коммітий!
2. Запусти тест з `-v --tb=long` для деталей
3. Виправ код
4. Запусти тест знову
5. Перевір регресію (`pytest -v`)
6. Тоді коммітий

---

## 🔄 CI/CD Integration (GitHub Actions)

Якщо у вас є GitHub Actions, регресійні тести запускаються автоматично при PR:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run tests
        run: cd backend && pytest -v
      - name: Upload coverage
        run: pytest --cov=backend --cov-report=xml
```

---

## 📝 Таблиця статусів тестів

| Статус | Символ | Дія |
|--------|---------|-----|
| Passed | ✓ | Все добре, коммітити можна |
| Failed | ✗ | Критична помилка, виправи перед коммітом |
| Skipped | ⊘ | Тест пропущений (OK, якщо це не критично) |
| Xfail | ✘ | Очікуєте падіння (OK для TO-DO тестів) |

---

## 🎓 Best Practices for AI-Agent

### Правило 1: ЗАВЖДИ запускай регресію перед коммітом

```bash
./run_checks.ps1  # Або ./run_checks.sh на Unix
```

### Правило 2: Якщо хоч один тест падає — ДЕ КОМІТИ!

```bash
# ❌ НЕПРАВИЛЬНО
git commit -m "Added new feature"  # Tests FAILED!

# ✅ ПРАВИЛЬНО
# 1. Fix the code
# 2. pytest -v → ✓ ALL PASS
# 3. git commit -m "Added new feature with tests"
```

### Правило 3: Регресія перевіряє ВСІ додатки

```bash
# ✅ Запусти ВСІ тести, не тільки свої
pytest -v  # Не тільки pytest telegram_api/tests.py
```

### Правило 4: Коли з'являється помилка

```bash
1. pytest -v --tb=long  # Отримай деталі
2. Знайди причину (читай помилку)
3. Виправ код
4. pytest -v  # Перевір ще раз
5. Якщо ВСІ тести зелені → коммітити
```

---

## 🔗 Запам'ятай

- **TDD:** Red → Green → Refactor
- **Regression:** Запусти ВСІ тести перед коммітом
- **Зелений статус:** ✅ — єдина дозволена умова для коммітки
- **run_checks.ps1:** Твій помічник перед коммітом

---

**Last Updated:** May 6, 2026
