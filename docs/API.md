# MyHaven API Reference Guide

**Version:** 1.1 | **Updated:** May 15, 2026

## Authentication
Most API endpoints require a valid JWT token.
- **Header**: `Authorization: Bearer <token>`
- **Token Acquisition**: `POST /api/token/`
- **Token Refresh**: `POST /api/token/refresh/`

## API Map

### 1. Users and Profiles (`/api/users/`)
- `POST register/`: Account creation.
- `GET me/`: Current authenticated user data.
- `GET/PATCH profile/`: Profile management.
- `POST change-password/`: Password updates.
- `POST delete-account/`: Account deletion.
- `GET export-data/`: JSON data export.
- `GET totp/setup/`: 2FA QR code generation.
- `POST totp/verify/`: 2FA verification.

### 2. Transactions (`/transactions/api/`)
- `GET dashboard/`: KPI summary.
- `GET statistics/`: Monthly data aggregation.
- `GET list/`: Filtered transaction list.
- `POST create/`: Manual entry.
- `GET/PATCH/DELETE <id>/`: Record management.
- `GET categories/`: Category list.
- `GET calendar/`: Calendar aggregate data.
- `POST uploads/`: Statement upload (PDF/Excel).

### 3. Budgets (`/api/budgets/`)
- `GET /`: Current month budget list.
- `POST /`: Budget creation.
- `GET/PATCH/DELETE <id>/`: Budget management.

### 4. Telegram API (`/api/telegram/`)
- `GET health/`: Connectivity check.
- `GET dashboard/`: Bot summary data.
- `GET transactions/`: Recent records.
- `POST transactions/`: Quick entry.
- `GET categories/`: Category list.

## Documentation and Schema
- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **OpenAPI Schema**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Common Status Codes
- **200 OK**: Request successful.
- **201 Created**: Resource created.
- **400 Bad Request**: Validation or syntax error.
- **401 Unauthorized**: Authentication required or invalid.
- **403 Forbidden**: Permission denied.
- **404 Not Found**: Resource not found.
- **500 Server Error**: Internal processing error.
