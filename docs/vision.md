# Vision

## Problem statement

Land management work — planting, restoration, invasive species treatment,
habitat interventions — mostly happens without a durable, structured record.
An individual restoring native plant habitat on their own property usually
ends up with some combination of memory, scattered photos, a spreadsheet,
and maybe a plant tag stuck in the ground. That record, such as it is,
almost never becomes something a neighbor, a visitor, or the broader public
can see or understand. At the other end of the spectrum, larger land
management organizations (land trusts, conservation programs, municipal or
institutional land managers) have the same underlying need — track
interventions across many properties or a large tract, with many people
contributing — but at a scale that a personal spreadsheet can't hold, and
usually with even less public visibility into ongoing or completed work.

There isn't a lightweight, purpose-built tool that:

1. Lets someone log what they did (or plan to do), where, and when, with
   enough structure to be queryable later — not just a diary entry.
2. Distinguishes "planned" from "done" so future work is visible, not just
   a historical log.
3. Turns that private log into a public-facing view of the land, without
   extra authoring effort.
4. Scales from a single yard to a multi-property organization without being
   rebuilt or re-architected along the way.
5. Eventually opens a path for the public to contribute back — observations,
   requests, feedback, or citizen-science-style data — in a form that's
   still TBD.

Habitat is meant to be that tool.

## Who this is for

- **Individual land managers.** Someone managing land they own or steward —
  the primary early persona is a homeowner doing native plant restoration on
  their own property. This is also the project's own first real user (see
  Roadmap, Phase 1).
- **Other individual homeowners / small-scale land managers** doing similar
  work on their own properties, who want the same logging and public-facing
  capability without needing an organization account.
- **Large land management organizations and programs** — land trusts,
  conservation nonprofits, municipal parks or natural resources departments,
  institutional land managers (e.g., a university or research station) —
  who manage many properties or large tracts, with multiple contributors
  working under one account/organization.
- **The public** — neighbors, visitors, community members, or anyone
  curious about what's happening on a piece of managed land, whether that
  land is a residential yard or a public conservation area.
- **Downstream programs and integrators** — other tools, dashboards, or
  research/citizen-science programs that want to consume Habitat data via
  an API rather than through the Habitat UI directly (e.g., a regional
  restoration-tracking dashboard, a research project aggregating planting
  data across many independent Habitat users).

## What success looks like

Early success is narrow and personal: the author uses Habitat to log their
own native plant restoration and yard management activity — plantings,
treatments, sightings — with locations, photos, and status, and it's
genuinely easier and more useful than a spreadsheet.

From there, success looks like:

- A visitor to the property (or its public page) can see, without asking,
  what's been planted, what's being treated, and what's planned next.
- Another homeowner doing similar restoration work can adopt Habitat for
  their own property with no changes needed to the underlying model.
- A land management organization can bring on many properties and many
  contributors under one account, with permissions that make sense for a
  team, without hitting limits baked in for the single-user case.
- A third-party program can pull Habitat data through an API — whether
  that's one homeowner's data or an organization's full portfolio — and
  build something on top of it.
- The public has some real, if not yet fully defined, way to contribute
  back to the record, not just view it.

Success is not, at this stage, a specific number of users or properties. It
is the data model and platform holding up, unmodified in its fundamentals,
across that entire range — from one yard to many large properties — while
staying simple enough for a single homeowner to actually use.
