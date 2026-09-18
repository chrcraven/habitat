import { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { api } from "../api/client";
import { PhotoLightbox, PhotoThumb } from "./PhotoLightbox";

/** Read-only photo grid for the public site — same visual shape as
 * PhotoUploader's grid (reuses .photo-grid/.photo-thumb) but with no
 * upload control and no delete button, since an anonymous visitor can do
 * neither. Fetches its own photos lazily per record rather than the
 * parent page loading every record's photos up front.
 *
 * Click-to-enlarge (F1) is deliberately on this path too, not just the
 * authenticated one: the bytes it shows are the same bytes this grid has
 * already downloaded, and an anonymous visitor could always reach them
 * with the browser's own "open image in new tab" (D6 declined
 * `Content-Disposition: attachment`). It exposes nothing that was not
 * already public. */
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
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  if (photos.loading || !photos.data || photos.data.length === 0) return null;

  const list = photos.data;

  return (
    <div className="photo-grid">
      {list.map((photo, i) => (
        <PhotoThumb
          key={photo.id}
          photo={photo}
          position={i + 1}
          total={list.length}
          onOpen={() => setLightboxIndex(i)}
        />
      ))}
      {lightboxIndex !== null && (
        <PhotoLightbox
          photos={list}
          index={lightboxIndex}
          onNavigate={setLightboxIndex}
          onClose={() => setLightboxIndex(null)}
        />
      )}
    </div>
  );
}
