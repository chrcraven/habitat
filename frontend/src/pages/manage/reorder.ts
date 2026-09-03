/**
 * Moving a row up or down in one of Manage's ordered lists (activity
 * types, workflow states).
 *
 * Both models carry an explicit `order` integer that the API has always
 * accepted — `docs/manual/limitations.md` claimed changing it "needs the
 * database directly", but it has been writable through the serializer the
 * whole time. So this is a frontend affordance over an existing endpoint,
 * not a new capability.
 *
 * Why rewrite every changed row rather than swapping the moved pair's two
 * `order` values: nothing has ever guaranteed the stored numbers are
 * distinct or gapless. The seeds write 0,1,2… but a type added through
 * the "Add" form takes `list.length` as its order, and two rows can end
 * up sharing a number (add two types, delete one in the middle, add
 * another). Swapping two equal values is a no-op the user sees as a
 * broken button. Normalizing to the array's own indices makes the list
 * self-healing instead: after any move, the order values are exactly
 * 0..n-1 in the order shown.
 */

/** Anything with an id and an order — both ActivityType and WorkflowState. */
export interface Orderable {
  id: number;
  order: number;
}

/** The list `items` with the item at `index` moved one slot in
 * `direction`. Returns the input unchanged if the move would fall off
 * either end. */
export function movedBy<T>(items: T[], index: number, direction: -1 | 1): T[] {
  const target = index + direction;
  if (index < 0 || index >= items.length || target < 0 || target >= items.length) {
    return items;
  }
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

/**
 * Move one row and persist the result. `update` is the API call for this
 * kind of row (`api.activityTypes.update` / `api.workflowStates.update`).
 *
 * Writes are sequential rather than concurrent: a normalizing pass can
 * touch several rows, and these lists are short enough that ordering the
 * requests costs nothing while keeping the server's view of a
 * half-applied move sane if one call fails partway.
 */
export async function moveRow<T extends Orderable>(
  items: T[],
  index: number,
  direction: -1 | 1,
  update: (id: number, data: { order: number }) => Promise<unknown>,
): Promise<void> {
  const reordered = movedBy(items, index, direction);
  if (reordered === items) return;
  for (let i = 0; i < reordered.length; i += 1) {
    if (reordered[i].order !== i) {
      await update(reordered[i].id, { order: i });
    }
  }
}
