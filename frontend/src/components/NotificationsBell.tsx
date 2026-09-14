import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import type { Notification } from "../api/types";

function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/**
 * In-app notifications bell — the one channel implemented so far in
 * backend/apps/notifications' pluggable dispatch (see /docs/open-
 * questions.md, "Task assignee notification"). Lives in TopBar so it's
 * visible from anywhere in the authenticated app, not just /tasks.
 *
 * Deliberately polls rather than pushing (no websocket infra in this
 * project) — a plain interval refetch, same "fine at current scale"
 * reasoning as Combobox's client-side filtering.
 *
 * This is the only list in the app that can show rows from an
 * organization other than the active one — `notification_list` filters on
 * the recipient alone, on purpose, because a notification is personal.
 * So it is also the only list that has to say which organization each row
 * is from, and to be honest about the fact that a row from elsewhere
 * can't be opened from here (D28, /docs/open-questions.md).
 */
export default function NotificationsBell() {
  const { data, reload } = useAsync(() => api.notifications.list(), []);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { session } = useAuth();
  const activeOrgId = session?.membership?.organization.id ?? null;

  /** Whether this notification belongs to an organization other than the
   * one the caller is currently acting in. Compares ids rather than
   * names, which is why the serializer sends both. When there's no active
   * membership we can't tell, so we don't claim anything. */
  const isFromAnotherOrg = (n: Notification) =>
    activeOrgId !== null && n.organization !== activeOrgId;

  useEffect(() => {
    const interval = setInterval(reload, 60_000);
    return () => clearInterval(interval);
  }, [reload]);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  // `results` is bounded by the server (NOTIFICATION_LIST_LIMIT), so it is
  // no longer the caller's complete history — it is exactly the rows this
  // panel shows, which is why nothing slices it again below.
  const notifications = data?.results ?? [];
  // Read the server's count; do NOT go back to
  // `notifications.filter((n) => !n.is_read).length`. That derivation was
  // correct only while the response carried every notification ever
  // received, and it is the reason bounding the list had to ship together
  // with this field rather than on its own: a user with 60 unread would
  // quietly see the bound instead, in a response that looks fine (D30).
  const unreadCount = data?.unread_count ?? 0;

  const handleOpenNotification = async (notification: Notification) => {
    if (!notification.is_read) {
      await api.notifications.markRead(notification.id);
      reload();
    }
    setOpen(false);
    // Only navigate for a task in the org we're actually acting in.
    // /tasks lists the *active* organization's tasks, so sending someone
    // there for another org's task lands them on a list that cannot
    // contain it — worse than not moving, because it reads as the task
    // having vanished. Until an org switcher exists (D28 Q1, the owner's
    // call) the honest behaviour is to mark it read and say where it
    // lives; see the row's own rendering below.
    if (notification.task && !isFromAnotherOrg(notification)) navigate("/tasks");
  };

  const handleMarkAllRead = async () => {
    await api.notifications.markAllRead();
    reload();
  };

  return (
    <div className="notif-bell" ref={containerRef}>
      <button
        type="button"
        className="notif-bell__toggle"
        onClick={() => setOpen((v) => !v)}
        aria-label={unreadCount > 0 ? `${unreadCount} unread notifications` : "Notifications"}
      >
        🔔
        {unreadCount > 0 && <span className="notif-bell__badge">{unreadCount}</span>}
      </button>
      {open && (
        <div className="notif-panel">
          <div className="notif-panel__header">
            <strong>Notifications</strong>
            {unreadCount > 0 && (
              <button type="button" className="btn-link" onClick={handleMarkAllRead}>
                Mark all read
              </button>
            )}
          </div>
          {notifications.length === 0 && <p className="muted notif-panel__empty">Nothing yet.</p>}
          <ul className="notif-panel__list">
            {notifications.map((n) => {
              const elsewhere = isFromAnotherOrg(n);
              return (
                <li key={n.id}>
                  <button
                    type="button"
                    className={
                      "notif-item" +
                      (n.is_read ? "" : " notif-item--unread") +
                      (elsewhere ? " notif-item--elsewhere" : "")
                    }
                    onClick={() => handleOpenNotification(n)}
                  >
                    <span>{n.message}</span>
                    {/* A notification from an organization you aren't
                        currently in. Naming it is the whole point: without
                        this the message reads as being about the org on
                        screen, and its task is nowhere in that org's task
                        list.

                        States the fact and stops — it deliberately does
                        NOT say "switch organizations to open it", because
                        there is no switcher (D28 Q1 is the owner's call).
                        Telling someone to do something the app gives them
                        no way to do is the D22 defect, and repeating it
                        here while fixing its sibling would be a poor
                        trade. */}
                    {elsewhere && (
                      <span className="notif-item__org">
                        In {n.organization_name} — not the organization you're in
                      </span>
                    )}
                    <span className="notif-item__time">{timeAgo(n.created_at)}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
