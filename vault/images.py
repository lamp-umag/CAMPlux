"""
Image file downloader -- added 2026-08-10. Until now the archive only ever
stored image_url (a link to the source site), which rots the moment that
site reorganizes or takes an old article down. This actually fetches and
keeps the bytes, alongside the existing text archive.

One shared images/ folder per Vault instance (not per-source), files named
by content hash -- naturally dedupes identical images (shared banners/
logos) regardless of which source(s) reference them, and means re-running
this is always safe (a hash that already exists on disk is just skipped).
"""
import hashlib
import os
import mimetypes
import requests

from scrapers.base import HEADERS

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15MB -- generous, but not "someone linked a video"
TIMEOUT_S = 20

_session = requests.Session()
_session.headers.update(HEADERS)


def _ext_for(content_type, url):
    ext = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if ext in (".jpe", None):
        # Fall back to the URL's own extension if the content-type is
        # missing/ambiguous (some CDNs serve images with no/odd Content-Type).
        url_ext = os.path.splitext(url.split("?")[0])[1].lower()
        if url_ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            return url_ext
        return ".jpg"
    return ext


def download_image(image_url):
    """Fetch image_url, save it under images/<hash>.<ext> if not already
    present. Returns the relative path (e.g. "images/ab/cdef123....jpg") on
    success, None on any failure -- callers should treat None as "try again
    another day", not a permanent failure, since it's often transient."""
    if not image_url or not image_url.startswith(("http://", "https://")):
        return None

    try:
        r = _session.get(image_url, timeout=TIMEOUT_S, stream=True)
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "")
        if "image" not in content_type and not any(
            image_url.lower().split("?")[0].endswith(e)
            for e in (".jpg", ".jpeg", ".png", ".gif", ".webp")
        ):
            return None  # not actually an image (e.g. an HTML error page)

        chunks = []
        total = 0
        for chunk in r.iter_content(8192):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                return None
            chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) < 200:  # implausibly small -- likely a 1x1 tracking pixel or broken fetch
            return None

    except requests.RequestException:
        return None

    digest = hashlib.sha256(data).hexdigest()
    subdir = digest[:2]
    ext = _ext_for(content_type, image_url)
    rel_path = os.path.join("images", subdir, f"{digest}{ext}")
    abs_path = os.path.join(DATA_DIR, rel_path)

    if os.path.exists(abs_path):
        return rel_path  # already have this exact image from elsewhere

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)
    return rel_path
