"""QR-code generation for public-site vanity URLs.

Generates a scannable PNG for a given public org/property URL, with an
optional image (e.g. an org logo) composited into the center. Because a
covered center loses part of the code, generation always uses the highest
error-correction level (H, ~30% recoverable) so the code still scans with
the logo over it — see /docs/open-questions.md ("QR code generator").

Kept as a plain module (not a view) so both the org and property QR
endpoints can share it. The endpoints build the absolute URL to encode
from a caller-supplied public-site origin plus the row's own slug (so a
generated code always points at that org/property's real public page), and
hand it here.
"""

import io

from django.conf import settings
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image

# Fraction of the QR's width the center logo is allowed to span. Kept
# conservative (25%) so that, combined with error-correction level H, the
# code stays reliably scannable with the logo covering its middle.
_LOGO_MAX_FRACTION = 0.25


def make_qr_png(url, logo_bytes=None):
    """Return PNG bytes for a QR code encoding `url`. If `logo_bytes` is
    given (raw bytes of an image file), it's scaled and pasted into the
    center on a small white pad so it reads as a deliberate emblem rather
    than corrupting the surrounding modules.

    Raises ValueError if `logo_bytes` isn't a decodable image, so the view
    can turn that into a clean 400 rather than a 500.
    """
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        except Exception as exc:  # Pillow raises a variety of errors here.
            raise ValueError("Could not read the center image.") from exc

        qr_w, qr_h = img.size
        target = int(qr_w * _LOGO_MAX_FRACTION)
        # Preserve aspect ratio, fit within a target x target box.
        logo.thumbnail((target, target), Image.LANCZOS)

        # White pad behind the logo so it doesn't blend into dark modules.
        pad = max(4, target // 12)
        box_w = logo.width + pad * 2
        box_h = logo.height + pad * 2
        backdrop = Image.new("RGB", (box_w, box_h), "white")
        backdrop.paste(logo, (pad, pad), logo)

        pos = ((qr_w - box_w) // 2, (qr_h - box_h) // 2)
        img.paste(backdrop, pos)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def public_base_url(raw):
    """The public-site origin to encode into a QR code.

    `settings.PUBLIC_SITE_URL` wins whenever it's configured: once a
    deployment says where the public site lives, the server knows better
    than the caller, and a QR code is a physical artifact that outlives the
    session that generated it — it shouldn't be able to point somewhere a
    client asked for. Blank (the default) falls back to the caller-supplied
    origin, which is how this worked before the public site could have its
    own origin: the SPA is on a different origin from the API, so the
    backend genuinely can't infer it otherwise. Returns the origin with any
    trailing slash stripped, or raises ValueError.
    """
    if settings.PUBLIC_SITE_URL:
        return settings.PUBLIC_SITE_URL
    if not raw:
        raise ValueError("A public site address is required.")
    raw = raw.strip().rstrip("/")
    if not (raw.startswith("http://") or raw.startswith("https://")):
        raise ValueError("The public site address must start with http:// or https://.")
    return raw
