# Table Talks — TODO and ideas

## Planned

- [ ] **Load questions from Google Sheet** — Replace or supplement CSV with a Google Sheet as the source for themes and questions (e.g. one sheet per theme, or a single sheet with theme + question columns). Use Google Sheets API and a service account or OAuth; keep CSV as fallback or for local dev.

## Ideas / improvements

- **Favorites / Bookmark Questions** — Let users save interesting questions to a favorites list. Add `/favorites` command to view saved questions later.
- **Random Mode Across All Themes** — "Surprise me" option that pulls random questions from all themes. Great for variety without committing to a single topic.
- **For users to suggest questions** — Let users submit new question ideas (e.g. a command or button "Suggest a question") and store them (file, sheet, or queue) for the owner to review and add to the deck.
- **Rate limiting** — Throttle per chat or per user to avoid abuse if the bot is public or shared widely.
- **Admin commands** — Optional `/stats` or `/broadcast` for the owner (e.g. how many chats, send a message to all); protect with a user-id allowlist.

## Code Quality / Refactoring

### High Priority

- **Themes Caching** — Add caching for `get_themes()` similar to `get_questions()`. Currently themes are loaded from CSV on every call.
- **Configuration Management** — Move hard-coded values (BOT_USERNAME, SECRET_LENGTH) to environment variables or config file for better configurability.
- **Session State Type Safety** — Improve SessionDict to enforce required fields and add support for new features (history, favorites).
- **Add More Tests** — Expand test coverage beyond data_loader. Add bot handler tests, integration tests, authorization tests, and session management tests.

### Medium Priority

- **Error Handling Improvements** — Enhanced error handler with specific handling for common Telegram errors (NetworkError, Timeout), user-friendly error messages, and error categorization.
- **Async File I/O** — Convert CSV reading to async using aiofiles for better async performance.
- **Logging Improvements** — Add structured logging (JSON format), correlation IDs for tracing, and performance timing logs.
- **Health Check Enhancement** — Expand health check to validate bot token, CSV file readability, and report memory usage stats.
