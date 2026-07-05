"""Single source of truth for the app version and release location.

Imported by the app (About Us page, update checker) and by the PyInstaller
.spec files, so the version lives in exactly one place. Bump __version__ here
before tagging a release.
"""

__version__ = "1.0.0"

# GitHub repository the in-app update checker looks at.
GITHUB_OWNER = "mdrayhan03"
GITHUB_REPO = "ShareBridge"

# Raw GitHub releases list (used as a fallback).
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

# Branded download landing page (GitHub Pages) — where the in-app "Download"
# button on an available update sends users.
DOWNLOAD_PAGE_URL = f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}/"
