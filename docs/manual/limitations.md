# Limitations & known gaps

Habitat is mid-build (Phase 1 complete, with a handful of Phase 2/3 slices
pulled forward — see `/CLAUDE.md`'s "Current phase" section for exactly
what that means). This page collects the user-facing gaps in one place so
they're easy to check before assuming something exists. For the technical
open-question versions of some of these (with more implementation detail),
see `/docs/open-questions.md`.

## Accounts & organizations

- **No org switcher.** If you belong to more than one organization, the
  app always acts as your first membership — which the top bar now names,
  so you can at least tell which one that is; see
  [Getting started](getting-started.md#which-organization-am-i-in). Two
  consequences follow. Being added to a *second* organization changes
  nothing you can see: that membership can never become the active one,
  and no notification announces it, so ask the admin who added you to
  confirm. And a task assigned to you in that other organization **does**
  reach your 🔔 notifications (they're addressed to you personally, not
  to an organization) — it's labelled with the organization it belongs
  to, but clicking it goes nowhere, because your Tasks page lists only
  the active organization's tasks. Visible, not reachable.
- **No real email delivery configured.** Inviting a new member (see
  [Organization admin](organization-admin.md#adding-a-member)) generates
  a real invite link and *tries* to email it, but no production email
  service is configured in this project yet — the admin portal always
  also shows a **Copy invite link** button as a fallback for exactly this
  reason. A password reset ("forgot password") flow **does** exist — see
  [Your account](account.md) — but it depends on that same missing email
  service, so in practice the reset link is only reachable by reading the
  server's console output. Unlike an invitation, it deliberately has no
  "copy the link" fallback in the admin portal: handing the link back
  would turn the reset form into a way to check whether a given email
  address has an account.

## Roles & permissions

- **A property-scoped admin can't hand off organization settings.** Their
  reach now stops at members scoped to their own properties (see [Roles
  and permissions](roles-and-permissions.md#what-a-property-scoped-admin-can-administer)),
  which also means renaming the organization, changing its public URL
  name or theme, authoring org-level pages, and reviewing feedback need
  an account-wide admin — there's no way to delegate one of those
  individually.
- **Roles are the fixed three.** viewer / editor / admin, optionally
  scoped to properties — no custom roles, and no per-feature permissions
  within a role.
- **A member scoped only to properties that get permanently removed
  becomes account-wide.** Habitat records "this member is scoped to
  everything" as an empty property list, so once the 30-day window closes
  and a property is removed for good, a member who was scoped only to it
  is left with an empty list and reads as account-wide — gaining access to
  the organization's other properties. Nothing like this happens while the
  property is merely deleted and restorable: for those 30 days the member
  stays scoped and sees nothing extra. **If you permanently remove a
  property, check Manage → Members afterwards** and re-scope (or remove)
  anyone who was assigned only to it. Making "scoped to nothing"
  something Habitat can represent properly is an open decision, not a
  behaviour to rely on.

## Records

- **You can't delete your last "finished" workflow state.** Your
  [workflow states](organization-admin.md#workflow-states) are yours to
  add, rename, reorder and delete, with one deliberate exception: at
  least one state must stay marked **Counts as finished work**, because
  that flag is the only thing telling the public map, your dashboard and
  the Activities filter which work is done. Un-flagging or deleting your
  only finished state is refused with an explanation. There's no such
  guard on the starting state — losing that one just means new activities
  start in whichever state is first.
- **Quick log doesn't keep a draft.** Backing out of a
  [quick log](dashboard.md#quick-log) mid-capture discards it. Quick log
  can't put species on an activity or link records — save the record and
  open it from its property to do those. (A *sighting's* species is on the
  details step, and a new one can be added there without leaving.)
- **A new species added while logging gets only its common name.** Both
  the quick-log details step and the sighting form create it from what you
  type; scientific name, description and bloom period stay blank until you
  fill them in on the [species page](species.md).
- **Species names are case-sensitive.** Habitat treats "Crabgrass" and
  "crabgrass" as two different species if you add them from the species
  page, and there's no merge tool to join them afterwards. The logging
  forms deliberately reuse a name you already have whatever its casing, so
  they won't create the pair for you.
- **Photos and header images must be PNG, JPEG, WebP or GIF.** SVG is
  refused on purpose, not by oversight: an SVG can contain a script, and
  because a photo on a public property has a shareable link that anyone can
  open, allowing them would let whoever uploaded the file run code against
  whoever opened that link. Vector logos need converting to PNG first. This
  applies to activity and sighting photos, to organization and property
  header images, and to a QR code's center image alike; in each case the
  picker only offers the accepted formats.
- **Photos are stored at whatever resolution you upload, and shown at
  thumbnail size.** Nothing resizes an upload — an 8 MB phone photo is
  kept in full, byte for byte — but the only place the app displays a
  photo is a small square in a grid. There is no click-to-enlarge or
  lightbox anywhere, so from inside Habitat you can't see the detail you
  captured; your browser's own "open image in new tab" on the thumbnail is
  the way to it. There's also no storage quota and no limit on how many
  photos a record can carry, so a busy account's database grows quickly.
  Both are known and being weighed — see `/docs/open-questions.md` — and
  the tradeoff isn't obvious, because generating a smaller copy to display
  either doubles what's stored or throws away detail a restoration record
  may want years later.
- **Repeat views of a page no longer re-download its photos** (since
  2026-09-14), which is worth knowing mainly because it explains a
  difference you may notice: the first time you open a property its photos
  come down in full, and after that your browser checks whether each one
  changed and is usually told "no" without the image being sent again.
  Measured on a six-photo page opened twenty times, that's 42.3 MB down to
  2.1 MB. Your browser still *asks* about every photo every time — that's
  deliberate, so that making a property private, or deleting a photo, takes
  effect immediately rather than after a cache expires.
- **You still can't add species or links while creating a record.** The
  create forms now offer photos right after saving, but species on an
  activity and links between records are still edit-form-only: save
  first, then reopen the record from its property.
- **The activity and sighting lists filter client-side.** The
  [Activities](activities.md#finding-an-activity) and
  [Sightings](sightings.md#finding-a-sighting) pages fetch all your
  records and search them in the browser — including the sightings map,
  which plots whatever that in-browser search currently matches. Fine at
  the scale a single organization reaches today; it isn't paginated or
  server-side search. (Those pages no longer make the *server* do
  needless work for each record — as of 2026-09-13 a list stops loading
  the header-image and photo data it never sends — but the browser still
  receives every record. Since 2026-09-14 responses are compressed in
  transit, which shrinks these lists severalfold; the record *count* sent
  is unchanged, and the map coordinates on an activity are the part that
  compresses least.)
- **Sightings can't be grouped, and only sightings have an org-wide map.**
  You can search the [Sightings](sightings.md#seeing-them-on-a-map) page
  for a species and see those points across every property, but there's no
  way to save that set as a named group, and nothing ties a run of related
  sightings together as one record. The Activities page has no equivalent
  map either — activities are drawn shapes rather than points, and an
  org-wide view of them hasn't been designed yet.
- **The nav is the same on every page.** A menu that changes with where
  you are was considered and deliberately parked for now.
- **Task assignment notifications are in-app only** — no email or push.
  See [Tasks](tasks.md#notifications).
- **The 🔔 bell shows your 20 most recent notifications, and older ones
  are kept but never deleted.** The bell has always shown about this many;
  what changed on 2026-09-14 is that the app now only *fetches* that many
  instead of re-downloading your entire notification history every minute
  on every screen. The unread badge still counts **all** your unread
  notifications, not just the twenty shown, so a large number there is
  accurate. There's no notification archive to page back through, no way
  to delete them, and nothing that ages them out — so the history grows
  for as long as the account exists. Nothing in the app makes that
  visible to you; **Mark all read** clears the badge but keeps the
  records. See [Tasks](tasks.md#notifications).
- **No due dates on tasks.**
- **No soft delete for anything except properties.** Deleting an
  activity, sighting, species, or task is immediate and permanent —
  see [Properties](properties.md#deleting-a-property) for the one place
  a delete is actually recoverable (30 days, admin-restorable). The one
  thing standing between you and an accidental permanent delete is the
  confirm prompt, so read it. For activities and sightings that prompt
  now says the delete can't be undone and counts the photos going with
  it; for a species or a task it's still only a bare "Delete … ?".
- **Deleting an activity or sighting deletes its photos too**, with no
  separate warning beyond the count in that confirm prompt and no way to
  get them back. Everything else in a record is text you could type
  again — the photos aren't.
- **Habitat shows who last changed a record, not what they changed.** An
  activity's edit form names whoever created it and whoever saved it last
  (a sighting names only its creator); there is no history beyond that.
  You can't see what a record looked like yesterday, what the previous
  value of a field was, or how many times it's been edited — only the most
  recent editor's name, which is overwritten by the next person to save.
  If you need to know what changed, you have to ask them.
- **Two people editing one record still silently overwrite each other.**
  Saving an activity writes back every field on the form using the values
  that were on screen when you opened it, so a colleague's change made in
  the meantime is reverted without a warning or a merge. Knowing who
  edited it last is a way to *notice* this, not a protection against it —
  reload before saving if the name isn't yours.
- **Some things record no attribution at all.** Properties, species,
  photos, activity types and workflow states have no "added by" anywhere —
  including, notably, photos, which are the one thing in the database that
  can't be re-typed if lost. Nobody is recorded as having uploaded one.
- **Attribution is an email address, and it's visible to every member.**
  There are no display names, so these read as raw addresses. Any member
  of your organization — including a viewer — can see who created or
  edited any record they can see. None of it reaches the public site.
- **Habitat itself doesn't back anything up.** There's no export, no
  scheduled dump, and no restore path anywhere in the app: if the
  database is lost, everything logged in it is gone. Whoever runs your
  deployment may well be backing the database up at the infrastructure
  level — that's outside Habitat and worth confirming with them rather
  than assuming, because nothing in the app will tell you either way.
- **A species in use can't be deleted at all.** Not a soft delete and not
  a recovery path — the delete is simply refused, naming the sightings
  and activities that still point at it, until you move them off it. See
  [Species](species.md#a-species-thats-in-use-cant-be-deleted).
- **No species merge/dedupe tool.**
- **A species' description is public, and there's no private notes
  field.** The description on the [species list](species.md) is shown to
  visitors on the public site by design; there's nowhere on a species to
  record something only your own members should see.
- **Tasks aren't shown on the public site** — they're an internal work
  item, not public-facing data. (Sighting↔activity links *are* now shown
  publicly — see [Public site](public-site.md).)

## Public site

- **You can't switch your organization page off.** Properties and records
  each have a public/private flag; the organization page itself has none,
  so it answers for every account whether or not anything has been
  published — showing your organization name, your theme, and an empty
  property list. Your organization name and its URL name are public by
  default for that reason (your email address is not — see
  [Public site](public-site.md#the-organization-page-itself-is-not-gated)).
  Whether to add an org-level switch, and what it should default to, is an
  open question — either default has a real cost, so it's deliberately not
  been decided unilaterally.
- **The only inventory of what you publish is the two record lists.**
  [Activities](activities.md#whats-on-the-public-site) and
  [Sightings](sightings.md#whats-on-the-public-site) each count and badge
  what's public, which covers the records that carry the flag — but
  nothing gathers your properties, pages and records into one "here is
  everything of ours that is currently on the internet" screen, and
  nothing records **when** something was published. Habitat can tell you
  what is public now; it can't tell you what changed, or when.
- **Nothing tells search engines anything.** Habitat ships no
  `robots.txt`, no `noindex` and no sitemap, so a crawler that finds a
  public page is not discouraged from indexing it. In practice the public
  site is a JavaScript app with no inbound links and no per-page titles,
  so it's unlikely to be indexed today — but that's a side effect, not a
  setting, and it isn't a guarantee. Whether Habitat should take a
  position here is an open question.
- **Publishing a property doesn't ask twice.** Ticking *Show this
  property on the public site* puts every public-marked activity and
  sighting on it online in one step. The record lists warn you how many
  that is beforehand, but the property form itself doesn't restate the
  number at the moment you tick the box.
- **No automatic, species-aware visibility.** A property has a
  [default public/private setting for new sightings](properties.md) an
  admin sets manually (e.g. for a preserve with an at-risk species) — but
  there's no automatic detection of "this species is sensitive" from the
  species list itself, and no location-fuzzing (showing an approximate
  area instead of the exact point) for a public sighting either.
- **No free-form CSS, and custom HTML is off unless it's switched on.**
  Public-site branding is limited to the fixed
  [Theme](organization-admin.md#theme) controls (colors, a font, a header
  image) — there's no free-text CSS field, and that's the deliberate
  final answer for styling rather than a step toward one.
  [Custom HTML pages](public-site.md#custom-html-pages) *do* now exist —
  your own HTML, CSS and JavaScript, run inside an isolated sandbox — but
  they're **off by default**: whoever runs your Habitat installation has
  to enable them, and can switch them off again for a single
  organization, so the Content type choice may simply not appear on your
  page form. A custom HTML page also doesn't inherit your theme, and is
  capped at 512 KB.
- **No content policy for author-published pages.** The sandbox around a
  custom HTML page stops author code reaching Habitat, other
  organizations, or anyone's login — but nothing stops an author
  publishing misleading content to their *own* page's visitors, and no
  written policy says what's allowed. The only remedy today is switching
  custom HTML off for that organization after the fact.

## Platform

- **In-app feedback isn't on by default.** The floating "Send feedback"
  button (for reporting bugs/friction/ideas about Habitat itself) is
  gated by a setting that's typically off on a given Habitat instance
  (e.g. off in production, on in a dev environment) — if you don't see
  it, that's expected, not a bug.
- **No public API yet.** Everything described in this manual is the
  logged-in app and the public *pages* — there is no documented,
  versioned API for third-party consumers. That's Phase 4 work.
- **The "page doesn't exist" screen is what you see, not what a machine
  is told.** A mistyped address shows a proper not-found page (see
  [Getting started](getting-started.md#an-address-that-doesnt-exist)), but
  the server still answers it with a normal "OK" status, because the whole
  app is served from a single fallback page. It reads correctly to a
  person; a link checker or search crawler won't recognise it as a dead
  address.
- **No rules-engine automation** (e.g. auto-suggesting a sighting↔activity
  link, auto-creating a task from a sighting). Deliberately deferred; see
  `/CLAUDE.md`.
- **Automated checks run on every change, but coverage is thin.** Since
  2026-09-05 every push and pull request runs the backend's Django checks
  and test suite against a real PostGIS database, and type-checks and
  builds the frontend. That's a floor, not a safety net: the backend suite
  is 220 tests across seven modules (public-site visibility, image uploads
  and limits, transport-security settings, feedback-token auth, cross-org
  species attachment, malformed request parameters, two admins editing
  membership at the same moment, adding the same species to one
  activity twice at once, the "forgot password" reply staying the same
  whoever asks, adding a species you already have, record lists not
  loading image data they never send, notifications saying which
  organization they belong to, the notification list staying a fixed
  size however long your history gets, and photos not being re-sent to a
  browser that already has them, and a member's email address reaching
  the person who needs it without reaching the public site), each added
  because something had already
  broken once rather than for coverage's own sake — so it is deliberately
  narrow, and whole features have no test at all.
  There's no frontend *test* runner either (only the typecheck and build).
  So if something looks broken, it's entirely possible no test covered it.

If you hit a gap that isn't listed here, it's worth checking
`/docs/open-questions.md` before assuming it's a bug — it may be a
deliberately deferred decision rather than an oversight.

---

[← Public site](public-site.md) · [Manual index](README.md)
