import { api } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import ThemeEditorPanel from "../../components/ThemeEditorPanel";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";

/** Public-site theme for the organization (colors, font, header image).
 * A property has its own theme controls on its own page; this is the
 * org-level default those fall back to, per field. */
export default function ThemeSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const org = useAsync(() => (allowed ? api.org.get() : Promise.resolve(null)), [allowed]);

  return (
    <ManageSectionPage
      title="Theme"
      access="account-admin"
      intro={
        <p className="muted">
          How your public site looks. A property can override any of these on its own page —
          anything you leave blank there falls back to what you set here.
        </p>
      }
    >
      {org.loading && <p className="muted">Loading…</p>}
      {org.error && <p className="form-error">Couldn't load organization: {org.error}</p>}
      {org.data && (
        <ThemeEditorPanel
          theme={org.data}
          onSave={async (data) => {
            await api.org.update(data);
            org.reload();
          }}
          previewImageUrl={api.org.themeImage.previewUrl}
          onUploadImage={async (file) => {
            await api.org.themeImage.upload(file);
            org.reload();
          }}
          onRemoveImage={async () => {
            await api.org.themeImage.remove();
            org.reload();
          }}
        />
      )}
    </ManageSectionPage>
  );
}
