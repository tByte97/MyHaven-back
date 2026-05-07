# ⚡ Quick Start — MyHaven Backend Development

**5 minutes to development** | May 6, 2026

---

## 🚀 Start (Копіпаста команди)

```bash
# 1. Clone & navigate
cd MyHavenProject/backend

# 2. Install (Windows)
pip install -r requirements.txt

# 3. Migrate DB
python manage.py migrate

# 4. Run tests (should all pass ✅)
pytest -v

# 5. Start server
python manage.py runserver

# 6. Open Swagger UI
# Browser: http://localhost:8000/api/docs/
```

---

## 📖 Read These First

| Priority | File | What | Time |
|----------|------|------|------|
| 🔴 **MUST** | [AI.md](AI.md) | Project map for AI agent | 5 min |
| 🔴 **MUST** | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | New dev onboarding | 10 min |
| 🟡 **SHOULD** | [TDD_GUIDE.md](TDD_GUIDE.md) | How to write tests | 15 min |
| 🟡 **SHOULD** | [.cursorrules](.cursorrules) | Code rules | 10 min |
| 🟢 **NICE** | [REGRESSION_TESTING.md](REGRESSION_TESTING.md) | Before commit checks | 10 min |

---

## ✅ Checklist Before Coding

- [ ] Read AI.md (5 min)
- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] DB migrated: `python manage.py migrate`
- [ ] Tests pass: `pytest -v` (should show 25 passed ✅)
- [ ] Server runs: `python manage.py runserver`
- [ ] Swagger UI open: http://localhost:8000/api/docs/
- [ ] Ready to code!

---

## 📂 Project Structure (30 seconds)

```
backend/
├── users/           # Auth & profiles
├── accounts/        # Bank accounts
├── transactions/    # Core: Parsing, categorization, KPI
├── budgets/         # Budget limits
├── telegram_api/    # Telegram bot API (NEW)
└── tests/           # Integration tests
```

**Remember:** Service layer pattern always:
```
View → Service → Repository → Model
```

---

## 🧪 Development Workflow (TDD)

### Step 1: Red (Test that FAILS)
```python
# backend/transactions/tests.py
def test_new_feature(self):
    result = some_function(data)
    self.assertEqual(result, expected)
```

Run: `pytest transactions/tests.py::test_new_feature -v` → ❌ FAILS

### Step 2: Green (Code that PASSES)
```python
# backend/transactions/services.py
def some_function(data):
    return expected
```

Run: `pytest transactions/tests.py::test_new_feature -v` → ✅ PASSES

### Step 3: Refactor (Clean up)
```bash
./run_checks.ps1  # Windows
# or
./run_checks.sh   # Unix
```

Runs: Tests ✓ + Linter (ruff) ✓ + Formatter (black) ✓

### Step 4: Regression (Verify nothing broke)
```bash
pytest -v
# Should show: 25+ passed ✅
```

---

## 🎯 Common Commands

```bash
# Tests
pytest -v                          # Run all tests
pytest users/tests.py -v          # Run app tests
pytest -k "export" -v             # Run tests with keyword "export"
pytest --cov=backend              # With coverage report

# Format & Lint
./run_checks.ps1                  # All checks (RECOMMENDED)
black backend/                    # Format code
ruff check backend/ --fix         # Fix lint issues

# Django
python manage.py migrate          # Apply migrations
python manage.py makemigrations   # Create migrations
python manage.py shell            # Python REPL with Django

# Server
python manage.py runserver        # http://localhost:8000/
python manage.py createsuperuser  # Create admin
```

---

## 🚫 BEFORE YOU COMMIT!

```bash
# 1. Run all checks
./run_checks.ps1

# 2. If all green → commit
git add .
git commit -m "feat: description"
git push origin branch-name

# 3. If any red → go back to TDD step 2
# FIX CODE → pytest -v → COMMIT
```

---

## 📞 Quick Help

| Problem | Solution |
|---------|----------|
| Tests fail | `pytest -v --tb=long` (see details) |
| Import error | Check `.cursorrules` (section "Common Issues") |
| Code formatting | `./run_checks.ps1` (auto-fix) |
| Confused where to write code | Read `DEVELOPER_GUIDE.md` (Architecture Decision Tree) |
| Want to understand architecture | Read `AI.md` (App Map section) |

---

## 🎓 Key Principles

1. **TDD Always:** Red → Green → Refactor
2. **DRY:** One function in one place (no copy-paste)
3. **SOLID:** One class = one responsibility
4. **Tests First:** Write test before code
5. **Regression Required:** Run all tests before commit
6. **AI.md is Truth:** It's the single source of facts

---

## 🤖 For AI Agent Users

If you're using Cursor AI or Claude:

```
You MUST:
1. Read AI.md first
2. Follow .cursorrules religiously
3. Write Red test → Green code → Refactor
4. Run: ./run_checks.ps1
5. Never commit if tests fail
6. Verify regression: pytest -v (all 25+)

You SHOULD:
- Use conftest.py fixtures (in backend/conftest.py)
- Add docstrings to all functions
- Use type hints everywhere
- Follow the service layer pattern

You MUST NEVER:
- Write logic in views.py
- Copy-paste code (DRY principle)
- Commit with red tests
- Skip regression testing
```

---

## 📚 Documentation Map

```
START HERE
    ↓
1. AI.md (5 min) ← What to build
    ↓
2. DEVELOPER_GUIDE.md (10 min) ← How to start
    ↓
3. TDD_GUIDE.md (15 min) ← How to develop
    ↓
4. .cursorrules (10 min) ← Code rules
    ↓
5. REGRESSION_TESTING.md ← Before commit
    ↓
START CODING! 🚀
```

---

## ✨ What You Have Now

- ✅ TDD workflow (Red-Green-Refactor)
- ✅ Auto-formatting (Black)
- ✅ Linting (Ruff)
- ✅ Tests (pytest with fixtures)
- ✅ API Documentation (Swagger UI)
- ✅ Regression protection (run_checks.ps1)
- ✅ AI guidelines (.cursorrules)
- ✅ Project documentation (AI.md)

---

## 🎯 Your First Task (Example)

```
Task: "Add function to get user's monthly balance"

1. Read AI.md → Understand project
2. Decide: Where? → services.py (business logic)
3. Write Red test → test fails ❌
4. Write Green code → test passes ✅
5. Run ./run_checks.ps1 → all green
6. Run pytest -v → regression OK
7. git commit → done! 🎉
```

---

## 🏁 Ready? Let's Go!

```bash
# Open terminal
cd MyHavenProject/backend

# Install & migrate
pip install -r requirements.txt
python manage.py migrate

# Run tests
pytest -v

# If all pass → START DEVELOPING!
python manage.py runserver

# And open Swagger UI:
# http://localhost:8000/api/docs/
```

---

**Questions?** → Read files in this order: **AI.md → DEVELOPER_GUIDE.md → TDD_GUIDE.md**

**Last Updated:** May 6, 2026 ✅
