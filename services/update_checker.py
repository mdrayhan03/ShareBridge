"""In-app update checker.

Asks the GitHub Releases API whether a newer version than the running one has
been published. Designed to fail silently: ShareBridge works fully offline, so
a failed or blocked check must never disrupt the app.
"""
import logging
import re

log = logging.getLogger(__name__)

GITHUB_API_LATEST = "https://api.github.com/repos/{owner}/{repo}/releases/latest"


def _parse_version(text):
    """Extract a numeric version tuple from strings like 'v2.0.0' or '2.1'."""
    match = re.search(r"(\d+(?:\.\d+)*)", text or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest, current):
    """True if version string `latest` is strictly newer than `current`."""
    lv, cv = _parse_version(latest), _parse_version(current)
    length = max(len(lv), len(cv))
    lv = lv + (0,) * (length - len(lv))
    cv = cv + (0,) * (length - len(cv))
    return lv > cv


def parse_release(payload, current_version):
    """Turn a GitHub release payload into update info, or None if not newer."""
    if not isinstance(payload, dict):
        return None
    tag = payload.get("tag_name") or payload.get("name") or ""
    if not tag or not is_newer(tag, current_version):
        return None
    return {
        "version": tag,
        "url": payload.get("html_url") or "",
        "notes": (payload.get("body") or "").strip(),
    }


async def fetch_latest_release(owner, repo, timeout=6.0):
    """Fetch the latest release payload from GitHub, or None."""
    import aiohttp

    url = GITHUB_API_LATEST.format(owner=owner, repo=repo)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ShareBridge-UpdateChecker",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as resp:
            if resp.status != 200:
                # 404 = no releases published yet; anything else = transient issue.
                log.info(f"Update: no release info (HTTP {resp.status})")
                return None
            return await resp.json()


async def check_for_update(current_version, owner, repo):
    """Return update info dict if a newer release exists, else None. Never raises."""
    try:
        payload = await fetch_latest_release(owner, repo)
    except Exception as e:
        log.info(f"Update: check skipped ({e})")
        return None
    return parse_release(payload, current_version)
