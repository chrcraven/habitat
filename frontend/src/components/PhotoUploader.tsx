import { useRef, useState } from "react";
import type { Photo } from "../api/types";

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
    try {
      await onDelete(photoId);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="photo-uploader">
      {error && <p className="form-error">{error}</p>}
      <div className="photo-grid">
        {photos.map((photo) => (
          <div key={photo.id} className="photo-thumb">
            <img src={photo.url} alt="" loading="lazy" />
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
          </div>
        ))}
        <label className="photo-add">
          {uploading ? "Uploading…" : "+ Photo"}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
            disabled={uploading}
            hidden
          />
        </label>
      </div>
    </div>
  );
}
