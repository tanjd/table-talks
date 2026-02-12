# Table Talks — TODO and ideas

## Planned

- [ ] **Load questions from Google Sheet** — Replace or supplement CSV with a Google Sheet as the source for themes and questions (e.g. one sheet per theme, or a single sheet with theme + question columns). Use Google Sheets API and a service account or OAuth; keep CSV as fallback or for local dev.

## Done

- [x] **Git repo** — Initialized git, `.gitignore`, conventional commits; pushed to remote.
- [x] Dockerize the app (Dockerfile + .dockerignore) for running on NAS.
- [x] **Health check** — HTTP GET `/health` on port 9999 (configurable via `HEALTH_PORT`); Docker `HEALTHCHECK` so the NAS/orchestrator can restart the container if the bot stops responding.
- [x] **CI** — GitHub Actions run `make check` on push/PR to main.
- [x] **CD** — On push to main, build and push Docker image (Docker Hub or GHCR; auth via repo secrets).

## Ideas / improvements

- **For users to suggest questions** — Let users submit new question ideas (e.g. a command or button “Suggest a question”) and store them (file, sheet, or queue) for the owner to review and add to the deck.
- **Persistence** — Persist `chat_data` (e.g. authorized chats, session state) across restarts using PTB’s `BasePersistence` (e.g. file or Redis) so secrets and progress survive reboots.
- **More themes and questions** — Grow `data/themes.csv` and `data/questions.csv` (or the future Sheet) with more themes and cards; consider community or curated packs.
- **Localization (i18n)** — If you want multiple languages, add a simple translation layer (e.g. gettext or a small dict) for bot messages and optionally for question content.
- **Rate limiting** — Throttle per chat or per user to avoid abuse if the bot is public or shared widely.
- **Admin commands** — Optional `/stats` or `/broadcast` for the owner (e.g. how many chats, send a message to all); protect with a user-id allowlist.
