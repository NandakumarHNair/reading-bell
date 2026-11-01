# Reading Bell deployment

Published on 1 November 2026.

- Repository: https://github.com/NandakumarHNair/reading-bell
- App: https://nandakumarhnair.github.io/reading-bell/
- Host: GitHub Pages, with HTTPS enforced
- Publishing source: `main`, `/(root)`

The application source is the Quiet Session Edition (2.0.0) supplied in the project ZIP. Its design and behavior were preserved.

## Verification

- Both inline JavaScript blocks passed syntax checks.
- A browser session confirmed that Space pauses and resumes without resetting the remaining time.
- A one-minute session reached completion normally.
- Entering 6.5 actual pages against 8 planned pages displayed 81.3%.
- Source inspection confirmed one start buzzer and one finish buzzer, silent pause/resume, and no recurring alarm or check-in paths.
- The app contains no outgoing network requests or remote scripts.

The included regression suite contains 47 checks. The previous archive reported that they passed, but that full suite was not rerun for this deployment because its test browser was unavailable. Browser UI checks were performed separately.

Physical sound and timing on locked or sleeping devices were not independently verified. Keep the page open and the device awake when relying on the finish buzzer.

## Updating

Edit the repository's `index.html` and commit to `main`. GitHub Pages rebuilds the site automatically; verify the deployment in the repository's Actions tab. The optional `publish.py` helper also supports updating this recognized Reading Bell repository using your own GitHub CLI sign-in.

Do not commit browser settings, personal reading results, imported fonts, credentials, or QA screenshots.
