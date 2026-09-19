import type { MembershipDetail, Task } from "../api/types";

/**
 * Who a task is assigned to, and whether that person is still a member —
 * the one rule behind every place this app names a task's assignee.
 *
 * Why this is a shared module rather than a ternary at each call site:
 * `TasksPage` renders the assignee twice, and the two disagreed (D47).
 * Read mode showed `assigned_to_email` verbatim — "Assigned to
 * volunteer@example.com". The edit control is a `Combobox` whose options
 * come from the member list, and `options.find((o) => o.id === value)`
 * cannot resolve an id that is no longer in it, so the same row's
 * assignee control fell back to its placeholder, "Unassigned". Two
 * controls, one row, two answers, and the authoritative-looking one was
 * the wrong one. Neither said the person had left.
 *
 * That state is reachable and permanent. `TaskSerializer.validate_assigned_to`
 * refuses to assign a task to a non-member with a 400 — but a task
 * assigned *before* a removal keeps pointing at that same non-member
 * indefinitely, because `Task.assigned_to` is `SET_NULL` on **User**
 * deletion and removing a `Membership` is not deleting a `User`. The
 * invariant is enforced at write time and never re-checked.
 *
 * What this deliberately does NOT do: change the assignment. Nulling a
 * dangling `assigned_to` is the attractive wrong fix — it answers "what
 * happens to their work?" (an open question for the owner, D47b's Q2) as
 * a side effect of a display fix, and it destroys the only record of who
 * was doing the work. This reports the state that already exists.
 */
export type AssigneeStatus =
  /** No `assigned_to` at all. */
  | { kind: "unassigned" }
  /** Assigned, and that person is in the org's current member list. */
  | { kind: "member"; email: string }
  /** Assigned to someone the member list does not contain — they were
   * removed from the organization after the task was assigned. */
  | { kind: "former"; email: string }
  /** Assigned, but the member list isn't known yet, so whether they are
   * still a member is genuinely unanswered — see `members` below. */
  | { kind: "unknown"; email: string };

/** Shown when a task carries an `assigned_to` id but no email came back
 * with it. Not reachable through the serializer as written
 * (`assigned_to_email` follows the same FK), but resolving it to "" would
 * render "Assigned to " and read as a rendering bug rather than a data
 * one. */
const UNNAMED = "someone no longer listed";

/**
 * @param members the organization's current members, or `null` when that
 *   list has not loaded yet (or failed to). The distinction is
 *   load-bearing and is the whole reason this takes a nullable rather
 *   than the `?? []` the call sites used to pass: `TasksPage` fetches
 *   tasks and members as two concurrent requests, so there is a real
 *   window in which the tasks have rendered and the member list has not
 *   arrived. Treating an empty-because-unloaded list as the member roster
 *   marks *every* assigned task "no longer a member" for that window —
 *   a fix that makes the app lie about everyone in order to stop it lying
 *   about one person. D39's lesson: unknown has to be a real answer.
 */
export function assigneeStatus(
  task: Pick<Task, "assigned_to" | "assigned_to_email">,
  members: MembershipDetail[] | null,
): AssigneeStatus {
  if (task.assigned_to === null || task.assigned_to === undefined) {
    return { kind: "unassigned" };
  }
  const email = task.assigned_to_email || UNNAMED;
  if (members === null) return { kind: "unknown", email };
  const isMember = members.some((m) => m.user.id === task.assigned_to);
  return { kind: isMember ? "member" : "former", email };
}

/** The qualifier appended to a former member's address. Kept as a named
 * constant because it is the entire user-visible content of D47a — the
 * change that would undo this fix is someone shortening it back to a bare
 * address. */
export const FORMER_MEMBER_SUFFIX = "no longer a member";

/** The assignee as a full sentence, for read-only display.
 *
 * `unknown` deliberately renders exactly like `member` — it states who
 * (which is known) and claims nothing about whether they are still a
 * member (which isn't). That way the settling of the member list only
 * ever *adds* the qualifier; it never retracts a claim this already made. */
export function assigneeSentence(status: AssigneeStatus): string {
  switch (status.kind) {
    case "unassigned":
      return "Unassigned";
    case "former":
      return `Assigned to ${status.email} — ${FORMER_MEMBER_SUFFIX}`;
    default:
      return `Assigned to ${status.email}`;
  }
}

/** The label a `Combobox` should show for the current value when its own
 * options can't resolve it — `undefined` when they can, or when there is
 * nothing assigned, in which case the control's placeholder is correct.
 *
 * This is the address and nothing else, deliberately. The first version
 * appended the qualifier here too, and at phone width the input rendered
 * "volunteer@example.com — no lon": an `<input>` clips its value to the
 * control's width, so the very words the fix exists to show were the ones
 * cut off, while `inputValue()` kept returning the whole string and every
 * assertion passed. A text input's visible width cannot be relied on to
 * carry meaning, so the control answers *who* and `assigneeFormerNote`
 * answers *what changed*, on its own line where it can wrap. */
export function assigneeValueLabel(status: AssigneeStatus): string | undefined {
  switch (status.kind) {
    case "former":
    case "unknown":
      return status.email;
    default:
      // "member" resolves from the options list itself; "unassigned" has
      // nothing to label.
      return undefined;
  }
}

/** The note shown beside an assignee control whose person has left —
 * `null` in every other state, including while the roster is still
 * loading, so this never flashes against a current member. */
export function assigneeFormerNote(status: AssigneeStatus): string | null {
  return status.kind === "former"
    ? "This person is no longer a member of this organization. The task stays assigned to them until someone reassigns it."
    : null;
}

/**
 * Confirm-dialog text for removing a member, naming how much live work
 * stays pointed at them.
 *
 * The D34 precedent, applied to people instead of photos: that dialog
 * ships "Its 3 photos are deleted too" because a number is what makes
 * someone stop, where "and any attached work" reads as boilerplate at
 * zero and badly understates it at twelve. The remove-member prompt was a
 * bare question.
 *
 * Note what this does *not* say: "this can't be undone". Unlike a delete,
 * a removal is reversible — an admin can add the same address back from
 * the form directly below this list. Borrowing the delete dialog's
 * closing line would be a false claim on a confirm prompt, which is the
 * defect class D19/D20 exist for.
 *
 * @param openTaskCount how many of that member's assigned tasks are still
 *   open (open or assigned — a resolved or dismissed task is a historical
 *   record, and counting those inflates the number until the warning is
 *   noise, which is how a control stops being read, per D45), or `null`
 *   if the count couldn't be fetched. `null` still warns, hedged: a
 *   removal must never be blocked, or made to look safe, because a count
 *   request didn't come back.
 */
export function confirmRemoveMemberMessage(
  email: string,
  openTaskCount: number | null,
): string {
  const head = `Remove ${email} from this organization?`;
  if (openTaskCount === null) {
    return `${head} Any tasks assigned to them stay assigned, and their name will show as a former member.`;
  }
  if (openTaskCount === 0) return head;
  // Singular matters: "1 open tasks are" is exactly the slip D30 shipped
  // ("All 1 sightings are plotted…"), caught only by looking at a
  // screenshot rather than at an assertion.
  const tasks =
    openTaskCount === 1
      ? "1 open task stays assigned to them"
      : `${openTaskCount} open tasks stay assigned to them`;
  return `${head} ${tasks}, showing their name as a former member.`;
}
