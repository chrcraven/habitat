/**
 * The image types the backend accepts on upload.
 *
 * This mirrors `ALLOWED_IMAGE_TYPES` in `backend/apps/accounts/images.py`,
 * which is the actual enforcement — this constant only steers the file
 * picker so a user isn't offered a file the server will then refuse with a
 * 400. Keep the two in step; the backend is the one that matters.
 *
 * Notably absent is SVG, which `image/*` would otherwise offer: it can
 * carry script, and the backend refuses it deliberately. See that module's
 * docstring for why.
 */
export const ACCEPTED_IMAGE_TYPES = "image/png,image/jpeg,image/webp,image/gif";
