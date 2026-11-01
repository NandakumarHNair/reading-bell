# Session regression tests

Install the development-only test dependencies:

```sh
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/session.py
```

The app itself has no dependencies. The runner also detects an installed `chromium` or `google-chrome`; set `CHROMIUM_EXECUTABLE` to override it. Screenshots are written to `tests/screenshots`, or to the `READING_BELL_QA` directory when provided.

The suite uses an isolated in-memory browser document and controlled time, Web Audio, and storage adapters. It checks **47 cases**, including:

- Start and finish cues only; no midpoint or repeated finish sound.
- Silent pause/resume, held-Space handling and cancellation of scheduled audio on reset.
- A finish-button click at the deadline does not double the buzzer.
- Editable reset, input validation, fractional pages, 0%, and results over 100%.
- Restoration without a duplicate start sound, and explicit audio re-enablement.
- Legacy settings migration without restoring recurring alarms or popups.
- Keyboard settings navigation, light/dark themes, and layouts at 320, 390, 768 and 1024 pixels.

A separate development smoke check exercised real Web Audio node creation and pause/resume in Chromium. These tests do not verify physical loudspeakers, exact real-device background timing, genuine persisted browser storage, iPhone hardware, or locked-screen alarms. Browser navigation was restricted in the build environment, so the automated suite deliberately operates in an isolated blank document rather than claiming a live-hosted deployment test.
