# Reading Bell — Quiet Session Edition

A self-contained reading session timer. A page target provides direction; there is no live pace score.

## Use

Open `index.html` in a modern browser, or serve it on an HTTPS static host. Enter **Pages to read** and **Minutes available**, then select **Start session**. No installation, build command, runtime dependency, account, or backend is required.

- One short, low buzzer at the start; one at the finish. No interval alarms, speech, desktop notifications, check-in popups, or repeating finish alarm.
- The target and time remain visible without ahead/behind feedback.
- After the session, enter actual pages read. Fractional pages are accepted. Completion is `actual pages / planned pages × 100`; it can exceed 100%. It is not a focus or learning score.
- Pausing and resuming are silent. **Space** pauses/resumes an active session, including when a control has focus. It no longer restarts an interval. Hold-to-repeat is ignored. Enter activates buttons; modified shortcuts remain unchanged.
- **Finish early** ends the session with one finish buzzer. **Reset & edit plan** cancels silently and returns to editable pages and minutes.
- Dark mode is the default. Clock/session view, focus view, appearance controls, local font import, floating display and multi-monitor windows are retained.

## Privacy and saved state

The app itself makes no network requests. Preferences use localStorage; the current session/result uses sessionStorage for reloads in the same tab. Storage can be disabled by the browser. Closing the tab may remove its session. Browser data is not synced across devices, different hosting addresses, or a local HTML file and a hosted version. Imported fonts remain in local IndexedDB and are not part of the project.

A restored running session keeps its deadline. Click **Enable finish buzzer** if audio permission is required after refreshing. No start sound is replayed.

## Reliability

The timer uses wall-clock deadlines, and the end buzzer is scheduled with Web Audio while audio is available. It does not depend on decrementing a JavaScript counter. However, browsers can suspend pages and audio: this website cannot guarantee locked-iPhone, sleeping-Mac, or closed-browser alarms. A late return may display completion with a late or unavailable finish sound. It is not a critical alarm.

Keep the page open and device awake. The optional screen wake lock works only when supported and permitted; it cannot override manual locking. Changes to device time can affect the deadline.

Official references:
- https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/state
- https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API

## Publish on GitHub Pages

GitHub Pages supports static HTML and is free with public repositories on GitHub Free. This archive is **prepared for deployment, not already deployed**.

Using GitHub CLI (`gh`) and Python 3.8+:

```sh
python3 publish.py
```

The helper uses your own GitHub CLI sign-in, asks before public publication, uploads an explicit list of project files, and configures branch-based Pages hosting. It never uploads browser settings, pages read, imported fonts, credentials, or QA screenshots. It does not replace an unrelated project or change an existing private repository to public. It reports the actual Pages address and build status; configuration alone is not proof that the site is live.

To choose a different repository name:

```sh
python3 publish.py --repo reading-bell-session
```

Alternatively, upload `index.html` and `.nojekyll` into a suitable public repository. In Settings → Pages, choose **Deploy from a branch**, the repository's actual default branch, and **/(root)**. Verify the resulting site after its build completes.

Official deployment documentation:
- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Tests

See `tests/README.md`. The included suite checks timer state, cancellation, keyboard behavior, page-completion calculations and responsive layouts. These tests are not a certification of locked-device audio.
