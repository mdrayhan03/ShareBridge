# Download Landing Page (GitHub Pages)

Instead of sending users to the raw GitHub Releases list, ShareBridge has a
branded download page that **auto-detects the visitor's OS** and **always points
at the latest release** — no manual updates when you ship a new version.

- Page source: `docs/index.html` (a single self-contained file — no build step)
- Hosted at: `https://mdrayhan03.github.io/ShareBridge/`

## How the "dynamic" part works

The page is static HTML, but its JavaScript calls the **GitHub Releases API** in
the visitor's browser:

```
GET https://api.github.com/repos/mdrayhan03/ShareBridge/releases/latest
```

That JSON contains:
- `tag_name` → shown as the version badge (e.g. `v2.0.0`)
- `assets[]` → each uploaded file's `name`, `size`, and `browser_download_url`

The script matches each asset to a platform by filename and fills in the
download buttons:

| Platform | Matches file name |
|----------|-------------------|
| Windows  | ends with `.exe` |
| macOS    | contains `mac` or ends `.dmg` |
| Linux    | contains `linux`, or ends `.AppImage` / `.tar.gz` |
| Android  | ends with `.apk` |

These line up with the artifact names produced by the CI pipeline
(`CI_RELEASE.md`). So the flow is fully hands-off: **push a tag → CI builds and
publishes a release → the page shows the new version and links automatically.**

It also detects the visitor's OS from the browser and highlights that platform's
card as the primary "Download" button.

## Enabling GitHub Pages (one-time)

1. Push `docs/index.html` to the `main` branch.
2. On GitHub: **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **Deploy from a branch**.
4. Set **Branch: `main`** and **Folder: `/docs`**, then **Save**.
5. Wait ~1 minute. Your page is live at
   `https://mdrayhan03.github.io/ShareBridge/`.

> You can point people at that URL from your portfolio, README, or the in-app
> "Download" button.

## Testing it locally

Open the file in a browser, or serve it (so the fetch behaves like production):

```bash
cd docs
python3 -m http.server 8000
# visit http://localhost:8000
```

Until you publish a release with build assets, the page shows a graceful
fallback ("Go to downloads" → the releases page). Once a release exists, the
buttons populate automatically.

## Good to know

- **No API token needed.** The releases API is public and CORS-enabled, so the
  browser can call it directly.
- **Rate limit:** unauthenticated GitHub API calls are limited to 60/hour *per
  visitor IP*. That's plenty for a normal download page. If the page ever became
  very high-traffic, you'd cache the response (e.g. via a tiny serverless proxy),
  but that's not needed at this stage.
- **Graceful fallback:** if the API is unreachable, blocked, or rate-limited, or
  there are no releases yet, every button falls back to the full releases page so
  users are never stuck.
- **Updating the design** is just editing `docs/index.html` — the version and
  download links are dynamic, so you never touch it for a new release.
