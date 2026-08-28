# Build Questions — awaiting owner input

Generated automatically on 2026-08-28 by a scheduled "resolve open questions"
task, from a full read of `docs/open-questions.md` (the durable source of
truth for unresolved decisions) plus the "Not done" notes trailing each
`CLAUDE.md` task-log entry. A push notification listing these went to the
account owner the same run this file was written.

**Status: unanswered.** Nothing below has owner input yet. The next
build/session should check this file first — if an item has since been
resolved (moved into `docs/open-questions.md`'s "Recently resolved" section
or otherwise decided), treat this file as stale for that item and update/
delete it accordingly rather than re-asking. Per this run's instructions, no
build was triggered — this is groundwork only.

## How to answer

Reply to the push notification, or just tell the next Habitat session your
answers directly and ask it to record them here and in
`docs/open-questions.md` — whichever's easier. Short answers are fine; a
narrowed-down default ("go with X unless you say otherwise") is also fine
for anything marked Medium/Low below.

---

## High priority — actively blocking or shaping near-term work

1. **Hosting/ops model.** Self-hosted vs. managed services? The Docker
   images now build and publish to Docker Hub on push to `main` (CI, as of
   2026-08-26/27/28), but that's just an image-publishing step — nothing
   is decided about where those images actually *run*, and the frontend
   image is still the dev server (`npm run dev`), not a production build
   behind a real static server. This blocks: an eventual production
   frontend Dockerfile, real SMTP configuration (below), and any answer to
   "is Habitat actually deployed anywhere yet."
2. **Real email delivery (SMTP provider).** Both the org-invite flow and
   the password-reset flow send mail through Django's `send_mail`, but
   `EMAIL_BACKEND` is still the console backend (logs only) — no provider
   chosen. The invite flow has a manual fallback (an admin can copy/share
   the accept link); the password-reset flow does **not** (returning the
   link directly would let the endpoint be used to enumerate registered
   emails), so "forgot password" is only really exercisable today by
   reading server logs. Picking a provider unblocks both flows for real
   use.
3. **Sensitive-species default visibility for sightings.** Per-record
   public/private is decided and built, but there's no auto-suggest/
   auto-set of "private" for a sighting of a known sensitive/at-risk
   species (e.g., an endangered species' exact public location can enable
   poaching/disturbance). Whoever logs a sighting today has to remember to
   flag it themselves. Worth resolving before any real Phase 2 rollout
   where the account owner might log a sensitive sighting, not just before
   Phase 5 public input.

## Medium priority — real gaps, not yet urgent

4. **Default workflow states for a brand-new account.** Status states are
   org-defined; what should a brand-new account start with out of the box
   (e.g. planned → in-progress → done) so a solo user isn't forced to
   design a workflow before logging their first activity?
5. **Are planned/done-equivalent states reserved?** The public map's
   planned-vs-done styling currently reads a plain `is_done` boolean off
   `WorkflowState`. Does every org-defined workflow have to designate which
   custom state(s) map onto "planned" vs "done," or is that looser than it
   sounds?
6. **Task status states.** Currently a fixed open → assigned → resolved
   (+ dismissed) set. Is that the real, final set, or should it also be
   org-customizable like activity workflow states?
7. **Task-assignment notification mechanism.** Nothing pings an assignee
   today — they have to check the `/tasks` page themselves. In-app only?
   Email (ties to question 2)? Something else?
8. **Should the public site surface the sighting↔activity link** (e.g.
   "reported by a visitor, treated on this date")? Good showcase of the
   public-input → management-action loop, not decided either way.
9. **Starter species list for a new account** — ships empty, or seeded
   with some common regional/native-plant defaults?
10. **Licensing of public data** once exposed via the public site or,
    later, the API — an explicit open-data license, all-rights-reserved
    with opt-in sharing, or something else?

## Lower priority — explicitly deferred, revisit later

11. **API design (REST vs GraphQL vs both), key issuance/rotation, rate
    limiting/access tiers** — all Phase 4, not evaluated in depth.
12. **Rule authoring, rule complexity, webhook reliability, auto-linking
    vs. human review** — all Phase 4/5 rules-engine questions, explicitly
    out of scope until then.
13. **Public input form and moderation** (Phase 5) — what public
    submissions look like and whether they need review before affecting
    the visible record.
14. **Property moving between accounts** (e.g. a homeowner's land formally
    adopted into a land trust program) — explicitly deferred as
    too open-ended until it's a concrete need.
15. **GIS import** (beyond the already-planned export) — likely a
    Phase 3/4-era concern.
16. **Slug/vanity public URLs** (`/public/org/mira-canyon-trust` instead
    of a numeric ID) — cosmetic, no functional blocker.
17. **Photo storage growth** at scale (DB size, backup cost, whether to
    cap/compress) — not urgent at current single-account scale.
18. **Social login / other auth options** beyond email+password.

---

*Source: `docs/open-questions.md` (full detail and rationale for every item
above lives there — this file is a prioritized, notification-friendly
summary, not a replacement for it) and the "Not done" notes in `CLAUDE.md`'s
task log.*
