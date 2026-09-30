import { useRef, useState } from "react";
import type { Photo } from "../api/types";
import { ACCEPTED_IMAGE_TYPES } from "../utils/images";
import { useAnnounce } from "./Announcer";
import { PhotoLightbox, PhotoThumb } from "./PhotoLightbox";

interface PhotoUploaderProps {
  photos: Photo[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (photoId: number) => Promise<void>;
  canDelete: boolean;
}

/** Shared by the Activity and Sighting edit pages — only available once a
 * record exists (photos are stored nested under /activities/<id>/photos/
 * or /sightings/<id>/photos/), so this doesn't appear on the *create*
 * forms. `capture="environment"` prefers the rear camera on a phone but
 * still falls back to a normal file picker everywhere else. */
export default function PhotoUploader({
  photos,
  onUpload,
  onDelete,
  canDelete,
}: PhotoUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const announce = useAnnounce();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const handleDelete = async (photoId: number) => {
    setDeletingId(photoId);
    setError(null);
    try {
      await onDelete(photoId);
    } catch (err) {
      // The `error` slot below was already here and already rendered —
      // handleFileChange above sets it — and this handler just didn't use
      // it, so a refused or failed delete left the thumbnail in place with
      // nothing said (D55, 2026-09-24). Fixed in the component rather than
      // at its three mount points (both edit forms and PostSavePhotoStep):
      // three copies of one guard is the shape D6 and D34 each paid for.
      //
      // Announced as well as rendered, using the same string (D57a,
      // 2026-09-24) — a deleted thumbnail is a purely visual confirmation,
      // so its *absence* tells a screen-reader user nothing at all.
      const message = err instanceof Error ? err.message : "Couldn't delete that photo.";
      setError(message);
      announce(message);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="photo-uploader">
      {error && <p className="form-error">{error}</p>}
      <div className="photo-grid">
        {photos.map((photo, i) => (
          <PhotoThumb
            key={photo.id}
            photo={photo}
            position={i + 1}
            total={photos.length}
            onOpen={() => setLightboxIndex(i)}
          >
            {canDelete && (
              <button
                type="button"
                className="photo-thumb__remove"
                onClick={() => handleDelete(photo.id)}
                disabled={deletingId === photo.id}
                aria-label="Delete photo"
              >
                ×
              </button>
            )}
          </PhotoThumb>
        ))}
        <label className="photo-add">
          {uploading ? "Uploading…" : "+ Photo"}
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES}
            capture="environment"
            onChange={handleFileChange}
            disabled={uploading}
            hidden
          />
        </label>
      </div>
      {/* Uploading a photo is editor-level and removing one is admin-only
        * (`ensure_role(ADMIN)` on both photo detail endpoints), so an
        * editor can put a photo on a record and not take it back off.
        * Without this the Remove button is simply absent — no refusal, no
        * reason, and no pointer to the one lever an editor does have
        * (D80, 2026-09-30). The absence is what the line exists to
        * explain, so it renders only once there is a photo to remove.
        *
        * It lives here rather than at the three mount points
        * (PostSavePhotoStep and both edit forms) because this component
        * already owns `canDelete` and already renders its own notes —
        * D33's chokepoint question, and the shape D6, D34 and D55a each
        * paid for.
        *
        * Deliberately names what the *action* requires, not what role the
        * reader has: whether a member should be told their own role is
        * D78, still the owner's, and D76's refusal set this precedent.
        * The publication clause is an "only if" on purpose — a record's
        * flag is necessary but not sufficient (its property must be
        * public too, and it must not be soft-deleted), so this stays true
        * whatever state the record is actually in. */}
      {!canDelete && photos.length > 0 && (
        <p className="field-hint muted">
          Removing a photo needs admin access — ask an organization admin. A photo is on the
          public site only if its record is, so clearing &ldquo;Show on the public site&rdquo; on
          the record retracts this one too, along with its notes, dates and any other photos.
        </p>
      )}
      {lightboxIndex !== null && (
        <PhotoLightbox
          photos={photos}
          index={lightboxIndex}
          onNavigate={setLightboxIndex}
          onClose={() => setLightboxIndex(null)}
        />
      )}
    </div>
  );
}
