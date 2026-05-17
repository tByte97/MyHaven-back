# MyHaven Backend Architecture and Technical Design

**Version:** 1.1 | **Updated:** May 15, 2026

## Project Scope
MyHaven is a system for personal finance management, featuring bank statement parsing, transaction categorization, and financial analytics via web and Telegram.

## Architectural Patterns

### 1. Service Layer Pattern
Business logic is contained within `services.py` modules. Views are restricted to handling request/response logic and delegating operations to services.

### 2. Repository Pattern
Data access logic is centralized in `repositories.py`. This provides a consistent interface for ORM queries and filtering.

### 3. Strategy Pattern
Bank statement parsing utilizes the Strategy pattern. Each bank format is handled by a specific parser implementation conforming to a shared interface.

### 4. SOLID Principles
The project adheres to SOLID design principles to ensure maintainability and scalability.

## Application Structure

| Application | Responsibility | Logic Overview |
|-------------|----------------|----------------|
| **core** | Configuration | Settings, routing, and middleware. |
| **users** | Auth and Profiles | JWT, 2FA, preferences, and data export. |
| **accounts** | Entities | Bank and Account management. |
| **transactions** | Core Operations | Parsing, categorization, and KPI calculation. |
| **budgets** | Limits | Monthly budget management. |
| **telegram_api** | Bot Integration | Specialized API endpoints for Telegram interaction. |

## Data Models
- **CustomUser**: User identity with profile and Telegram metadata.
- **Bank and Account**: Storage entities for financial data.
- **Category**: System and user-defined transaction classifications.
- **Transaction**: Core financial unit linked to accounts and categories.
- **Budget**: Monthly category-based expenditure limits.

## Technical Stack
- **Framework**: Django 5.2.7, Django REST Framework 3.16.1.
- **Database**: PostgreSQL.
- **Authentication**: JWT (djangorestframework-simplejwt).
- **API Documentation**: OpenAPI 3.0 (drf-spectacular).
- **Parsing**: pdfplumber, openpyxl, pandas.
- **Security**: pyotp, cryptography.
