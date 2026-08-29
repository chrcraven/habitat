import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
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
 */
export default function NotificationsBell() {
  const { data, reload } = useAsync(() => api.notifications.list(), []);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

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

  const notifications = data ?? [];
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleOpenNotification = async (notification: Notification) => {
    if (!notification.is_read) {
      await api.notifications.markRead(notification.id);
      reload();
    }
    setOpen(false);
    if (notification.task) navigate("/tasks");
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
            {notifications.slice(0, 20).map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  className={"notif-item" + (n.is_read ? "" : " notif-item--unread")}
                  onClick={() => handleOpenNotification(n)}
                >
                  <span>{n.message}</span>
                  <span className="notif-item__time">{timeAgo(n.created_at)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
