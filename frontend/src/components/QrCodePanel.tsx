import { useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

/**
 * Generates and previews a downloadable QR code for a public URL. Kept
 * generic — the caller supplies `fetchQr` (which posts to the right org or
 * property QR endpoint) so the same panel serves both the org admin portal
 * and a property page. An optional center image (e.g. a logo) can be
 * embedded; the backend uses a high error-correction level so the code
 * still scans with it. See backend apps/accounts/qrcodes.py.
 */
export default function QrCodePanel({
  fetchQr,
  downloadName,
  publicUrl,
}: {
  fetchQr: (logo?: File | null) => Promise<Blob>;
  downloadName: string;
  publicUrl: string;
}) {
  const [logo, setLogo] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Track the object URL so we can revoke the previous one on regenerate /
  // unmount rather than leaking it.
  const urlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    };
  }, []);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const blob = await fetchQr(logo);
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      setPreviewUrl(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate the QR code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qr-panel">
      <p className="muted qr-panel__url">
        Public link: <code>{publicUrl}</code>
      </p>
      <label className="field">
        <span>Center image (optional)</span>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setLogo(e.target.files?.[0] ?? null)}
        />
        <span className="field-hint muted">
          Embed a logo or image in the middle of the code — it stays scannable.
        </span>
      </label>
      {error && <p className="form-error">{error}</p>}
      <div className="qr-panel__actions">
        <button type="button" className="btn btn-secondary btn-small" onClick={generate} disabled={loading}>
          {loading ? "Generating…" : previewUrl ? "Regenerate" : "Generate QR code"}
        </button>
        {previewUrl && (
          <a href={previewUrl} download={downloadName} className="btn btn-primary btn-small">
            Download PNG
          </a>
        )}
      </div>
      {previewUrl && (
        <img src={previewUrl} alt="QR code for the public URL" className="qr-panel__preview" />
      )}
    </div>
  );
}
