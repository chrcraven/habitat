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
- **Nobody can leave an organization, and no account can be deleted.**
  Only an admin can remove a member — a viewer or editor has no way to
  remove their own membership, there's no account-closure or
  account-deletion anywhere in the app, and there's no way to delete an
  organization either. The last-admin protection means a solo owner
  can't even remove themselves from their own organization. So the
  relationship only runs one way: an organization can remove you; you
  can't leave.
- **Removing a member doesn't retract what was already sent to them.**
  They lose access to the organization immediately, and no new
  notification can reach them — but notifications they received while
  they were a member stay in their own 🔔 list, naming the organization,
  for as long as their account exists. Nothing is ever purged.
- **Removing a member doesn't unassign their tasks.** Those keep their
  name, now labelled as a former member (see
  [Tasks](tasks.md#when-an-assignee-leaves)) — deliberate, so the record
  of who was doing the work survives, but it does mean a departure leaves
  work sitting in someone's name until a person reassigns it. Habitat
  won't do it for you and won't remind you again after the removal
  prompt.
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

- **Nothing in Habitat knows a planned date has passed.** You can give an
  activity a planned date, and Habitat will store it, show it and sort by
  it — but it never compares it to today. There is no "overdue" anywhere:
  no badge, no warning, no filter, no count, and no way to ask "what
  slipped?". An activity planned for last November and one planned for next
  spring are treated identically, because the only thing that makes an
  activity "still to do" is whether someone has marked it done. That
  matters most on your [dashboard](dashboard.md): the
  **Planned / in progress activities** section is sorted soonest-first and
  shows five, so the *oldest* slipped work fills it, and genuinely upcoming
  work can be pushed out of view. Nothing is lost or hidden from the
  Activities page — but if you need to know what's late, you have to read
  the dates yourself. Whether Habitat should have a notion of "overdue" at
  all is an open question, not an oversight: a restoration plan dated
  "spring 2026" isn't late in March.
- **Nothing stops a sighting being dated in the future.** Dates aren't
  validated against today in either direction, and the Sightings list and
  property map both sort newest-observed-first — so a mistyped year (2027
  for 2026) pins that sighting to the top of both until you correct it.
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
- **Photos are stored at whatever resolution you upload.** Nothing resizes
  an upload — an 8 MB phone photo is kept in full, byte for byte. Since
  2026-09-18 you can click a thumbnail to see that full-size image, so the
  detail you captured is reachable from inside Habitat rather than only
  through your browser's "open image in new tab". What hasn't changed is
  what's *stored*: there is still no smaller copy, no storage quota and no
  limit on how many photos a record can carry, so a busy account's
  database grows quickly. That one is known and being weighed — see
  `/docs/open-questions.md` — and the tradeoff isn't obvious, because
  generating a smaller copy either doubles what's stored or throws away
  detail a restoration record may want years later.
- **Photos have no caption, title or description.** There is nowhere to
  record what a photo shows, which means a screen reader can only announce
  its position ("Photo 2 of 3") and never its content, and you can't search
  or sort by anything about a photo. Nothing displays the date a photo was
  taken either, even where the camera recorded one.
- **Habitat has never been tested with a screen reader, and has no
  accessibility commitment.** Worth stating precisely rather than
  alarmingly, because most of what you might assume is missing is
  present: every image has alt text, every form field has a label, the
  browser's focus outline is left intact everywhere, the page has proper
  landmarks, text scales with your browser's font size, and every text
  colour pair meets WCAG AA contrast. As of 2026-09-24 the pickers also
  announce which option the arrow keys have landed on, failed deletions
  are announced rather than only shown, and a record card you can pin to
  the map announces itself as a button. What has **not** happened is
  anyone driving the app with an actual screen reader, or committing to a
  conformance target — so there is no claim here that Habitat meets one.
  Specific things still known to be missing: only the five destructive
  deletions announce their failures (every other error message is shown
  but not announced), moving keyboard focus between record cards does not
  move the map the way scrolling does, and changing page does not announce
  the new page or move focus to it.
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
  transit, which shrinks these lists severalfold. As of 2026-09-21 the
  screens that show a list and *no* map — Home, Activities and Tasks —
  also stop asking for the map shapes they were never going to draw,
  which is most of what was left: measured on 10,000 activities, 680 KB
  down to 117 KB. The Sightings page deliberately keeps them, because it
  plots its results. As of 2026-09-22 your **property boundaries** skip
  the same way on the six screens that only ever show property *names* —
  Properties, Home, Activities, Sightings, and Manage's Members and
  Recently-deleted sections — which matters more per property than it
  sounds, because a boundary you walked has far more points than a shape
  you drew: measured, about 90% of that list's compressed size at twenty
  properties. Quick log deliberately keeps them, because it works out
  which property your pin landed on. The record *count* sent is still
  unchanged.)
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
- **A failed delete tells you, but doesn't offer to retry.** Deleting a
  property, activity, sighting or photo now reports the reason if it
  doesn't go through, instead of looking like a button that did nothing.
  What it doesn't do is offer a "try again" — you press Delete yourself,
  which also means confirming the prompt a second time.
- **One delete still stays quiet: removing an authored page from a
  property's own page.** Deleting the same page from **Manage → Pages**
  reports a failure; doing it from the property's Pages section doesn't,
  so a failure there shows only as the page not disappearing from the
  list. Deliberate rather than an oversight — the list staying put is
  itself the signal on that screen — but it does mean the two routes to
  the same action behave differently.
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
  Any member of your organization — including a viewer — can see who
  created or edited any record they can see. None of it reaches the
  public site. Display names do exist (see the next bullet), but
  attribution doesn't use them: every "added by" and "last edited by"
  line in Habitat reads as a raw address even for people who have a name
  on file.
- **A name can only be set when the account is created, and the person
  who starts the organization is never asked for one.** Habitat stores a
  first and last name, and shows it in two places — the "Welcome back"
  greeting and the member list. Whoever *joins* by invitation is asked
  for their name on the accept screen, so they get one. Whoever *creates*
  the organization by signing up is not asked, so they don't — which
  means the owner is usually the one person in their own organization
  with no name. There is no profile screen and no other way to add one
  afterwards: an admin can change your role and your property scope, but
  not your name, and there's nothing on the Account page for it either.
  If you want a name on your own account today, the only route is to have
  been invited into an organization rather than to have started one.
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
- **A property whose URL name was already `explore` or `pages` keeps
  it.** Those two are now refused for new and renamed properties (see
  [Properties](properties.md)), because the public site uses them in the
  same position for your organization's own Explore view and authored
  pages. Nothing went back and changed properties that already had one —
  renaming is a live URL change, and Habitat won't make that decision for
  you. If a property's public address doesn't reach it, give it a
  different **Public URL name** on its edit page; the numeric address
  (`/public/properties/<id>`) works throughout either way.
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
  is 375 tests across seven modules (public-site visibility, image uploads
  and limits, transport-security settings, feedback-token auth, cross-org
  species attachment, malformed request parameters, two admins editing
  membership at the same moment, adding the same species to one
  activity twice at once, the "forgot password" reply staying the same
  whoever asks, adding a species you already have, record lists not
  loading image data they never send, notifications saying which
  organization they belong to, the notification list staying a fixed
  size however long your history gets, and photos not being re-sent to a
  browser that already has them, and a member's email address reaching
  the person who needs it without reaching the public site, and sign-in
  and sign-up being rate-limited per device, and the server being able to
  say honestly whether it is working, and a deployment that configured a
  mail server being told when its mail is silently going nowhere, and an
  email address being checked for the shape of an email address before it
  is stored — while sign-in and password reset deliberately keep accepting
  anything, so an account created before that check can still get in, and
  adding somebody to your organization never rewriting the name on their
  account, and expired sign-in sessions actually being cleared out of the
  database rather than kept forever, and a list that leaves out map
  shapes actually leaving them out rather than fetching them twice, and
  an activity or sighting logged before Habitat started recording who
  logged it still being editable, and a property never being given a
  public URL name that the public site's own addresses would swallow),
  each added
  because something had already
  broken once rather than for coverage's own sake — so it is deliberately
  narrow, and whole features have no test at all.
  There's no frontend *test* runner either (only the typecheck and build).
  So if something looks broken, it's entirely possible no test covered it.

- **Only two things are rate-limited, and nothing is limited per
  account.** Since 2026-09-17 signing in and signing up are capped per
  device (roughly ten sign-in attempts a minute, five new accounts an
  hour). Nothing else in Habitat has a rate limit or a quota: there is no
  cap on how many properties, records, species or members an organization
  can create, no storage quota, and no plan or tier concept anywhere. The
  two that exist were added because they are the only unauthenticated
  requests that cost the server real work; the rest simply hasn't been
  needed yet at this project's size.
- **Each list tells you how many it's showing, but there's no single
  "what do we have?" screen — and photos can't be counted at all.** Since
  2026-09-21 the Properties, Activities, Sightings, Species, Tasks and
  Members screens each state their own count. What doesn't exist is a
  place that puts those together, and there is no way at all to ask how
  many photos your organization has or how much space they take: photos
  are reachable only one record at a time, so nothing can total them.
  The one place Habitat ever counts photos is the confirmation prompt
  when you delete a record, which tells you how many are about to go with
  it. Combined with the fact that nothing resizes an upload (see
  "Photos are stored at whatever resolution you upload" under **Records**)
  and that there's no storage quota, an organization can accumulate a lot
  without any screen mentioning it.

- **Habitat checks that an email address is *well-formed*, but not that
  it's *real*.** Since 2026-09-19, signing up and inviting a member both
  refuse an address that isn't a valid email address at all — `chris@`,
  `not an email`, a missing `@`, or one longer than 254 characters. What
  no check can tell you is whether the address belongs to anyone: there is
  no confirmation email and no verification step, so `chris@gmial.com`
  (one transposed letter) is accepted exactly like the address you meant.
  Your browser doesn't save you here either — a typo in a real-looking
  address is valid to it too.

  This is worth knowing because of what it costs to get wrong. If you
  mistype your address at sign-up, **a password reset can't tell you** —
  that page deliberately gives everyone the same reply whether or not an
  account exists (see [Your account](account.md)), so a wrong address and
  a working one look identical. An *invitation* is more forgiving: the
  admin who sent it can copy the invite link straight out of
  [Organization admin](organization-admin.md) and pass it to you another
  way. Check your address when you sign up.
- **An account, and the organization created with it, can't be deleted
  from inside the app.** There's no "close my account", no way to remove a
  user, and no way to delete an organization — a *membership* can be
  removed (see [Organization admin](organization-admin.md)), which takes
  someone out of an organization but leaves their login intact. Whoever
  runs your Habitat instance can do it directly in Django admin; there is
  no self-service route.

If you hit a gap that isn't listed here, it's worth checking
`/docs/open-questions.md` before assuming it's a bug — it may be a
deliberately deferred decision rather than an oversight.

---

[← Public site](public-site.md) · [Manual index](README.md)
