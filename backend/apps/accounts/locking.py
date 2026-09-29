"""The one lock in this backend, and the class of guard that needs it.

# The shape

A **check-then-act** guard reads a count or an existence, decides the
write is safe, and then writes — with nothing held between the two
statements. `settings.py` sets no `ATOMIC_REQUESTS`, so each statement
autocommits on its own connection. Two requests arriving at the same
moment therefore both read the *pre-write* state, both pass the check,
and both write: the system lands in exactly the state the guard exists
to prevent, and neither request sees an error.

Every such guard in Habitat protects a *last one of something* in an
organization, so they are all serialized the same way: take a row lock
on the `Organization`, then do the read and the write inside that
transaction.

# Why the organization row, and not the rows being counted

The rows a competing request would change are not necessarily the rows
this request read — the two admins in the classic case are demoting
*different* memberships — so locking what you read does not help. The
organization is the thing both requests have in common, which is what
makes it the thing to serialize on.

It also has to be a row lock rather than `select_for_update()` on the
count query itself: D16's count is a `DISTINCT` over a join, and
Postgres rejects `FOR UPDATE` alongside `DISTINCT`.

# Why this module exists rather than a private helper

It shipped in D16 as `_lock_organization` inside `apps/accounts/views.py`
— with a docstring that stated the class in general terms, one app away
from three guards that matched it word for word and took nothing:
`WorkflowStateViewSet.destroy`'s "needs at least one workflow state" and
"your only state marked as finished", and
`WorkflowStateSerializer.validate`'s `is_done` un-flag guard. Naming the
class correctly in a place only one caller could see it is the same
failure as D6's content-type check copy-pasted four times and D74's
"narrow PATCH is safe" citation being true of the method somebody looked
at and false of the next one down. See D75 in /docs/open-questions.md.

# What a caller has to get right

Taking the lock is not enough on its own — the **check has to happen
after it**, in the same transaction as the write. A lock taken after the
count has already been read serializes nothing while looking entirely
correct in a diff.

Two things this has to be, measured against seven variants when D75
extended it (the table is in `apps/activities/tests.py`):

* **The organization row, not the rows being counted.** Locking the
  counted rows is the near-miss: it passes every behavioural test,
  because locking all of an org's workflow states does serialize the
  requests that race over them. It is still wrong, because it locks a
  *set* whose acquisition order is undefined — `WorkflowState`'s
  `Meta.ordering` ends in `order`, which carries no uniqueness
  constraint, so two states can share one and two transactions can take
  them in opposite orders. A non-total ordering (D2, D30, D70) turns
  into a deadlock here. An empty set also locks nothing, and a second
  serialization point for one organization's invariants is how the next
  guard takes the wrong one.

* **One lock, held across the whole check-and-write.** Where the check
  lives in a serializer and the write in `perform_update()`, that means
  the view wraps the entire DRF cycle — see
  `WorkflowStateViewSet.update`.

Guards for one organization that live in different entry points have to
share this lock, not take one each: D75's sharpest case is a DELETE
racing a PATCH, which a per-path lock leaves wide open with both
requests still returning success.

A concurrency test alone cannot hold any of that down — a race that
happens to serialize on a fast machine passes against broken code
(D16/D17/D18's standing lesson) — so each guard is pinned by a mechanism
test asserting *which* row is locked.

Reads that cannot *reduce* the protected count don't contend for the
lock and shouldn't take it — creating a membership or a workflow state
only ever raises it.
"""

from .models import Organization


def lock_organization(organization):
    """Block until this organization's other count-reducing writes finish.

    Call inside `transaction.atomic()`, *before* the guard's own read.
    The returned row is rarely what a caller wants; the lock is.
    """
    return Organization.objects.select_for_update().get(pk=organization.pk)
