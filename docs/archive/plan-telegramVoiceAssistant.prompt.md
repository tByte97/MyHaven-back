## Plan: Telegram bot + assistant MVP

Build a shared assistant service in the backend that handles intents and tool calls (stats + transactions), expose it via web chat and Telegram webhook, and add Telegram voice-to-text using Faster Whisper while storing only metadata.

**Steps**
1. Create a new Django app for assistant features with models that store only metadata (user, channel, message id, timestamps, detected intent, tool usage, status, latency) and explicitly exclude message content and audio.
2. Implement an assistant service layer that normalizes input (text/voice), calls ASR for voice, routes to tools, and builds responses; reuse existing repository/service logic for transactions and stats while enforcing safe actions and validation.
3. Add a provider abstraction for LLM and ASR (Faster Whisper) in settings-driven config so you can swap hosted or local models without changing orchestration logic.
4. Add REST endpoints for web chat in the new app (authenticated) and wire them into core routing; keep payloads small and return structured assistant responses plus metadata ids. *Depends on step 1-3*
5. Implement Telegram webhook handling that resolves `telegram_user_id` to the user, supports linking flow (one-time code from web settings), downloads voice files, runs ASR, calls the assistant service, and replies via the Bot API. *Depends on step 2-3*
6. Add a minimal chat UI on the website with a message list + input, wired to the new API; add routing and store methods following existing client patterns. *Parallel with step 5 after API contract in step 4*
7. Add tests for assistant orchestration (tool routing, transaction create/update), web chat endpoint, and Telegram webhook payload parsing; add docs for setup, tokens, and webhook registration. *Depends on step 4-5*

**Relevant files**
- [AI.md](AI.md) -- architecture rules and service/repository patterns to follow
- [backend/telegram_api/views.py](backend/telegram_api/views.py) -- existing Telegram endpoints and helper patterns
- [backend/telegram_api/urls.py](backend/telegram_api/urls.py) -- routing style for API endpoints
- [backend/users/models.py](backend/users/models.py) -- Telegram user fields for linking
- [backend/transactions/repositories.py](backend/transactions/repositories.py) -- stats and filtering used by the assistant tools
- [backend/transactions/services.py](backend/transactions/services.py) -- transaction creation workflow patterns
- [backend/core/urls.py](backend/core/urls.py) -- API route registration
- [client/src/stores/api.js](client/src/stores/api.js) -- API call patterns for the client
- [client/src/router/index.js](client/src/router/index.js) -- route registration pattern

**Verification**
1. Run backend tests for the new app and telegram handling with `python manage.py test`.
2. Manual: send a Telegram text and voice message, verify text response and metadata logged (no content stored).
3. Manual: open the web chat, ask for stats and create a transaction, confirm DB changes via the UI or admin.

**Decisions**
- Recommended: Telegram webhook delivery (fallback to long-polling if no public URL).
- Recommended: one-time linking code from web settings to connect Telegram user id to account.
- LLM provider: build an interface and start with a hosted provider for speed, keeping a local option available.
- Scope: exclude TTS for now; keep replies text-only.

**Further Considerations**
1. If you must avoid external APIs, plan for a local LLM (e.g., llama.cpp) and run Faster Whisper in the same service container; expect higher hardware requirements.
2. If you later need voice replies, add a TTS provider and Telegram audio reply support as a separate phase.
