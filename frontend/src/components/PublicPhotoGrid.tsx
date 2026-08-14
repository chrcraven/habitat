import { useAsync } from "../hooks/useAsync";
import { api } from "../api/client";

/** Read-only photo grid for the public site — same visual shape as
 * PhotoUploader's grid (reuses .photo-grid/.photo-thumb) but with no
 * upload control and no delete button, since an anonymous visitor can do
 * neither. Fetches its own photos lazily per record rather than the
 * parent page loading every record's photos up front. */
export default function PublicPhotoGrid({
  kind,
  id,
}: {
  kind: "activity" | "sighting";
  id: number;
}) {
  const photos = useAsync(
    () => (kind === "activity" ? api.public.activityPhotos(id) : api.public.sightingPhotos(id)),
    [kind, id],
  );

  if (photos.loading || !photos.data || photos.data.length === 0) return null;

  return (
    <div className="photo-grid">
      {photos.data.map((photo) => (
        <div key={photo.id} className="photo-thumb">
          <img src={photo.url} alt="" loading="lazy" />
        </div>
      ))}
    </div>
  );
}
