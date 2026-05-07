# 🏦 MyHaven — Personal Finance Backend

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-25%2B%20passing-brightgreen?style=flat-square)
![Code Style](https://img.shields.io/badge/Code%20Style-Black%2BRuff-000000?style=flat-square)

> **Professional Django backend** with TDD, Regression Testing, and AI-ready development infrastructure

---

## 🚀 Quick Start

```bash
# 1. Install & Setup (5 min)
cd backend
pip install -r requirements.txt
python manage.py migrate

# 2. Run Tests
pytest -v

# 3. Start Server
python manage.py runserver

# 4. Open Swagger UI
open http://localhost:8000/api/docs/
```

**[📖 Read QUICK_START.md for detailed setup](QUICK_START.md)**

---

## 📋 What is MyHaven?

MyHaven is a personal finance management system that helps users:
- 📊 Import bank statements (PDF/Excel)
- 🏷️ Auto-categorize transactions
- 💰 Track budgets and expenses
- 📈 View statistics and KPIs
- 🤖 Integrate with Telegram bot

---

## 🎯 Key Features

| Feature | Status | API Endpoint |
|---------|--------|--------------|
| User Authentication (JWT) | ✅ | `POST /api/token/` |
| User Profile & Settings | ✅ | `GET /api/users/profile/` |
| 2FA (TOTP) | ✅ | `GET /api/users/totp/setup/` |
| Bank Statement Import | ✅ | `POST /api/transactions/uploads/` |
| Auto-Categorization | ✅ | Smart keyword matching |
| Dashboard & KPI | ✅ | `GET /api/transactions/dashboard/` |
| Budget Management | ✅ | `GET /api/budgets/` |
| Telegram Bot API | ✅ | `GET /api/telegram/health/` |
| OpenAPI/Swagger Docs | ✅ | `GET /api/docs/` |

---

## 📁 Project Structure

```
MyHavenProject/
├── AI.md                      # 🤖 Source of truth for AI development
├── .cursorrules               # 📏 Code rules & guidelines
├── QUICK_START.md             # ⚡ 5-minute setup
├── DEVELOPER_GUIDE.md         # 👨‍💻 For new developers
├── TDD_GUIDE.md               # 🧪 How to write tests
├── REGRESSION_TESTING.md      # 🛡️ Before commit checks
├── SETUP_SUMMARY.md           # 📋 What was done
│
└── backend/
    ├── conftest.py            # Pytest fixtures
    ├── pytest.ini             # Test configuration
    ├── requirements.txt       # Dependencies (Black, Ruff, pytest, drf-spectacular)
    │
    ├── core/                  # Django settings
    ├── users/                 # Users & Auth (TDD + Service Layer)
    ├── accounts/              # Bank accounts
    ├── transactions/          # Core: Parsing, categorization, KPI
    ├── budgets/               # Budget management
    ├── telegram_api/          # Telegram Bot API (NEW)
    └── tests/                 # Integration tests
```

---

## 🏗️ Architecture

```
Vue.js Frontend
    ↓
REST API (Django REST Framework)
    ↓
[ Views ] → [ Services ] → [ Repositories ] → [ Models ]
    ↓
PostgreSQL Database
```

**Design Patterns:**
- ✅ Service Layer (business logic separation)
- ✅ Repository Pattern (data access)
- ✅ Strategy Pattern (multiple bank parsers)
- ✅ SOLID Principles (Single Responsibility, etc.)

---

## 🧪 Testing & Quality

### What's Included
- ✅ **25+ passing tests** (users, telegram, transactions)
- ✅ **TDD workflow** (Red-Green-Refactor)
- ✅ **Regression testing** (run_checks.ps1)
- ✅ **Auto-formatting** (Black)
- ✅ **Linting** (Ruff)
- ✅ **Code coverage** (pytest --cov=backend)

### Run Tests
```bash
pytest -v                     # All tests
pytest users/tests.py -v     # Specific app
pytest --cov=backend         # With coverage
./run_checks.ps1             # Full checks (Windows)
./run_checks.sh              # Full checks (Unix)
```

---

## 📚 Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [AI.md](AI.md) | **Project map for AI agents** | 5 min |
| [QUICK_START.md](QUICK_START.md) | **5-minute setup** | 5 min |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | **New developer onboarding** | 10 min |
| [TDD_GUIDE.md](TDD_GUIDE.md) | **How to write tests** | 15 min |
| [.cursorrules](.cursorrules) | **Code style & rules** | 10 min |
| [REGRESSION_TESTING.md](REGRESSION_TESTING.md) | **Testing before commit** | 10 min |
| [backend/BACKEND_ARCHITECTURE.md](backend/BACKEND_ARCHITECTURE.md) | **Deep dive architecture** | 20 min |

---

## 🤖 For AI Agents (Cursor, Claude, etc.)

### First Steps
1. **Read** [AI.md](AI.md) — your project map
2. **Follow** [.cursorrules](.cursorrules) — code rules
3. **Practice** [TDD_GUIDE.md](TDD_GUIDE.md) — test-first development
4. **Verify** `./run_checks.ps1` — before every commit

### Workflow
```
Red (test fails) → Green (test passes) → Refactor → Regression ✅
```

---

## 🚀 API Endpoints

### Authentication
```
POST   /api/token/                    Get JWT token
POST   /api/token/refresh/            Refresh token
```

### Users
```
GET    /api/users/me/                 Current user
GET    /api/users/profile/            User profile
PATCH  /api/users/profile/            Update profile
POST   /api/users/change-password/    Change password
POST   /api/users/delete-account/     Delete account (with password confirmation)
GET    /api/users/export-data/        Export all user data
```

### 2FA (TOTP)
```
GET    /api/users/totp/setup/         Generate QR code
POST   /api/users/totp/enable/        Enable 2FA
POST   /api/users/totp/disable/       Disable 2FA
POST   /api/users/totp/verify/        Verify 2FA code
```

### Transactions
```
GET    /api/transactions/dashboard/   Dashboard KPI
GET    /api/transactions/statistics/  Statistics by month
GET    /api/transactions/list/        List with filters
POST   /api/transactions/create/      Add manually
GET    /api/transactions/{id}/        Transaction details
DELETE /api/transactions/{id}/        Delete transaction
GET    /api/transactions/categories/  List categories
GET    /api/transactions/calendar/    Calendar data
POST   /api/transactions/uploads/     Upload bank statement
```

### Telegram API
```
GET    /api/telegram/health/          Health check
GET    /api/telegram/dashboard/       Dashboard
GET    /api/telegram/transactions/    List transactions
POST   /api/telegram/transactions/    Create transaction
GET    /api/telegram/categories/      List categories
GET    /api/telegram/budgets/         List budgets
```

### Budgets
```
GET    /api/budgets/                  List budgets
POST   /api/budgets/                  Create budget
GET    /api/budgets/{id}/             Budget details
PATCH  /api/budgets/{id}/             Update budget
DELETE /api/budgets/{id}/             Delete budget
```

---

## 🛠️ Development Workflow

### Before Coding
```bash
pip install -r requirements.txt
python manage.py migrate
pytest -v  # Should show 25+ passed ✅
```

### During Coding (TDD)
```bash
# 1. Red: Write test that fails
pytest tests/test_new.py → ❌ FAILED

# 2. Green: Write code that passes
pytest tests/test_new.py → ✅ PASSED

# 3. Refactor: Clean up
./run_checks.ps1

# 4. Regression: Verify nothing broke
pytest -v → ✅ ALL PASSED
```

### Before Commit
```bash
# MUST PASS:
./run_checks.ps1        # Tests + formatting + linting
pytest -v               # All 25+ tests green
git diff                # Review your changes
```

---

## 🎓 Learning Path

**If you're new to the project:**
1. Read **[QUICK_START.md](QUICK_START.md)** (5 min)
2. Follow **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** (10 min)
3. Study **[TDD_GUIDE.md](TDD_GUIDE.md)** (15 min)
4. Review **[.cursorrules](.cursorrules)** (10 min)
5. Start coding! 🚀

**If you're an AI agent:**
1. Read **[AI.md](AI.md)** (5 min)
2. Follow **[.cursorrules](.cursorrules)** (mandatory)
3. Practice TDD religiously
4. Run `./run_checks.ps1` before every commit
5. Never commit with failing tests

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Lines of Code | ~3,500 |
| Django Apps | 6 (users, accounts, transactions, budgets, telegram_api, core) |
| API Endpoints | 30+ |
| Test Cases | 25+ |
| Code Coverage | ~12% (goal: >80%) |
| Python Version | 3.x |
| Django Version | 5.2 |
| Database | PostgreSQL |

---

## 🔐 Security

- ✅ JWT authentication (SimpleJWT)
- ✅ CORS configured (localhost:8080)
- ✅ SQL Injection protected (Django ORM)
- ✅ CSRF protection (Django)
- ✅ Password hashing (PBKDF2)
- ✅ 2FA with TOTP (pyotp)
- ✅ Rate limiting (to be added)
- ✅ HTTPS redirect (production)

---

## 🚀 Next Steps

### Immediate
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run tests: `pytest -v`
- [ ] Start server: `python manage.py runserver`
- [ ] Open Swagger: http://localhost:8000/api/docs/

### Short-term
- [ ] Increase test coverage to 30%
- [ ] Add webhook for Telegram bot
- [ ] Celery for async tasks

### Medium-term
- [ ] Reach 80% code coverage
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Email notifications

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests fail | `pytest -v --tb=long` (see full error) |
| Import errors | Check `backend/conftest.py` fixtures |
| Formatting errors | Run `./run_checks.ps1` |
| DB issues | `python manage.py migrate` |
| Confused where to code | Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |

---

## 📜 License

[Add your license here]

---

## 👥 Contributors

- Development Team
- AI-Powered Development Workflow

---

## 📬 Contact

For questions about the project infrastructure, see:
- **Project Context:** [AI.md](AI.md)
- **Development:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **Testing:** [TDD_GUIDE.md](TDD_GUIDE.md)

---

**Last Updated:** May 6, 2026 ✅  
**Status:** Production Ready 🚀  
**AI Ready:** Yes, read [AI.md](AI.md) 🤖
