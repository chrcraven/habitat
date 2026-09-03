import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import PhotoUploader from "./PhotoUploader";
import type { Photo } from "../api/types";

/**
 * The "add photos now?" step a create flow shows after saving, instead of
 * navigating straight away.
 *
 * Photos are nested under a saved record's id, so this can only exist
 * after the save — which is exactly why the create forms never offered
 * it and made you save, reopen the record, and upload from the edit form
 * instead. Quick log set the precedent on 2026-09-03 by adding this step;
 * this is that step extracted so the ordinary activity and sighting forms
 * can share it rather than growing their own copies of the same six
 * handlers.
 *
 * PhotoUploader already prefers the rear camera on a phone
 * (`capture="environment"`), so none of this is new capability — it's
 * somewhere in the flow to use what already existed.
 */
export default function PostSavePhotoStep({
  kind,
  recordId,
  onFinish,
}: {
  kind: "activity" | "sighting";
  recordId: number;
  /** Where the flow goes from here. Both "Skip" and "Done" call it, so a
   * create flow ends in the same place it always did. */
  onFinish: () => void;
}) {
  const { session } = useAuth();
  // Photo delete is admin-only on the backend (ensure_role), same as
  // everywhere else PhotoUploader is used.
  const canDelete = roleAtLeast(session?.membership?.role, "admin");
  const [photos, setPhotos] = useState<Photo[]>([]);

  const photoApi = kind === "sighting" ? api.sightings.photos : api.activities.photos;

  const uploadPhoto = async (file: File) => {
    const photo = await photoApi.upload(recordId, file);
    setPhotos((current) => [...current, photo]);
  };

  const deletePhoto = async (photoId: number) => {
    await photoApi.remove(recordId, photoId);
    setPhotos((current) => current.filter((p) => p.id !== photoId));
  };

  return (
    <div className="page">
      <div className="page__header">
        <h1>Add photos</h1>
        <button type="button" className="btn btn-ghost btn-small" onClick={onFinish}>
          Skip
        </button>
      </div>
      <p className="muted">
        Your {kind} is saved. Add photos now while you're still there, or skip — you can always add
        them later by editing the record.
      </p>
      <PhotoUploader
        photos={photos}
        canDelete={canDelete}
        onUpload={uploadPhoto}
        onDelete={deletePhoto}
      />
      <button type="button" className="btn btn-primary" onClick={onFinish}>
        {photos.length > 0 ? "Done" : "Done — no photos"}
      </button>
    </div>
  );
}
