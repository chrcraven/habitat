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

# An uploaded center image is bounded twice, because the two bounds stop
# different things and neither implies the other.
#
# MAX_LOGO_BYTES bounds the transfer and the read() into memory. Django's
# DATA_UPLOAD_MAX_MEMORY_SIZE looks like it already does this and does not:
# it deliberately exempts file fields. Measured against Django 5.2.17's real
# MultiPartParser at this repo's own 10MB setting — 25MB as a *text* field
# raises RequestDataTooBig, while 25MB and even 200MB as a *file* field
# parse fine. That exemption is exactly why the four other image endpoints
# each carry their own `image.size >` check, and settings.py's own comment
# says so. 5MB matches MAX_THEME_IMAGE_BYTES: a center image is the same
# kind of asset as a theme banner (an org's own brand mark), so the two
# should not disagree about what "too big to send" means.
MAX_LOGO_BYTES = 5 * 1024 * 1024

# MAX_LOGO_PIXELS bounds the *decode*, which the byte count does not — and
# this is the load-bearing half. A flat-colour 9000x9000 PNG compresses to a
# ~250KB file that costs ~300MB of resident memory and several seconds of
# CPU to decode, so it slips under any byte cap (and under any edge proxy's
# body-size limit) untouched.
#
# Pillow's own DecompressionBomb guard does not cover this. It only engages
# above Image.MAX_IMAGE_PIXELS (89,478,485) — warning there, raising above
# 2x — so an image can sit an order of magnitude beneath it and still be
# ruinous. Measured: 9000x9000 emits no warning at all and returns 200.
#
# 16 megapixels is far above anything legitimate here: the logo is
# thumbnailed to 25% of the QR's width, a couple of hundred pixels, so even
# a full-resolution phone photo (~12MP) passes with room to spare.
MAX_LOGO_PIXELS = 16_000_000

UNREADABLE_LOGO_MESSAGE = "Could not read the center image."

OVERSIZE_LOGO_MESSAGE = "The center image is too large (max 5MB)."

TOO_MANY_PIXELS_MESSAGE = (
    "The center image's dimensions are too large. It is only shown a couple "
    "of hundred pixels wide, so please use a smaller image."
)


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
        # Split deliberately across three steps rather than the one chained
        # expression this used to be. Image.open() is lazy — it parses the
        # header and exposes .size *without* decoding the pixels — so the
        # dimension check below costs nothing and, crucially, happens before
        # the decode it exists to prevent. Chaining .convert() back onto the
        # open() would decode first and make the guard pointless.
        try:
            logo = Image.open(io.BytesIO(logo_bytes))
        except Image.DecompressionBombError as exc:
            # Pillow's own guard, which fires at open() above 2x its
            # MAX_IMAGE_PIXELS — far beyond MAX_LOGO_PIXELS, so this only
            # catches the extreme tail our check never gets to see. Answered
            # with the dimensions message rather than "could not read"
            # because it is the same user mistake, just larger: the two
            # guards compose, and they should say the same thing.
            raise ValueError(TOO_MANY_PIXELS_MESSAGE) from exc
        except Exception as exc:  # Pillow raises a variety of errors here.
            raise ValueError(UNREADABLE_LOGO_MESSAGE) from exc

        width, height = logo.size
        if width * height > MAX_LOGO_PIXELS:
            # Raised outside the try/except above on purpose: this is a
            # refusal with its own actionable message, not a failure to read
            # the file, and wrapping it would flatten it into "could not
            # read" and tell the user the wrong thing to fix.
            raise ValueError(TOO_MANY_PIXELS_MESSAGE)

        try:
            logo = logo.convert("RGBA")
        except Exception as exc:
            raise ValueError(UNREADABLE_LOGO_MESSAGE) from exc

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
