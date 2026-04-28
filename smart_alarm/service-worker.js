/*  service-worker.js  — Smart Alarm background engine
    Served from /static/ but registered at scope "/" via the Flask route.

    Flow:
      1. Main page sends  { type: 'SET_ALARM',   delayMs: <ms> }
      2. SW waits delayMs, then fires a system notification.
      3. Main page sends  { type: 'CANCEL_ALARM' } to clear the timer.
*/

let alarmTimer = null;

// ── Message handler ──────────────────────────────────────────────
self.addEventListener("message", (event) => {
  const data = event.data || {};

  if (data.type === "SET_ALARM") {
    // Clear any existing pending alarm
    if (alarmTimer) clearTimeout(alarmTimer);

    const delayMs = Math.max(0, data.delayMs);

    alarmTimer = setTimeout(() => {
      self.registration.showNotification("⏰ Wake Up! — Smart Alarm", {
        body:             data.label
                            ? `Your alarm for ${data.label} is ringing!`
                            : "Your Smart Alarm is ringing!",
        icon:             "/static/icon-192.png",   // optional — add a PNG here
        badge:            "/static/icon-192.png",
        vibrate:          [400, 200, 400, 200, 600],
        requireInteraction: true,                   // stays visible until dismissed
        tag:              "smart-alarm",            // replaces itself if re-fired
        renotify:         true,
        actions: [
          { action: "stop",   title: "⏹ Stop Alarm" },
          { action: "snooze", title: "💤 Snooze 5 min" },
        ],
      });

      alarmTimer = null;
    }, delayMs);

    console.log(`[SW] Alarm scheduled in ${Math.round(delayMs / 1000)}s`);
  }

  if (data.type === "CANCEL_ALARM") {
    if (alarmTimer) {
      clearTimeout(alarmTimer);
      alarmTimer = null;
      console.log("[SW] Alarm cancelled");
    }
  }
});

// ── Notification click handler ───────────────────────────────────
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "snooze") {
    // Reschedule 5 minutes later
    const snoozeMs = 5 * 60 * 1000;
    alarmTimer = setTimeout(() => {
      self.registration.showNotification("⏰ Snooze Over! — Smart Alarm", {
        body:               "Time to wake up for real now!",
        icon:               "/static/icon-192.png",
        vibrate:            [400, 200, 400, 200, 600],
        requireInteraction: true,
        tag:                "smart-alarm",
        renotify:           true,
      });
    }, snoozeMs);
    return;
  }

  // Default: focus the app tab (or open it)
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      const existing = list.find((c) => c.url.includes(self.location.origin));
      if (existing) return existing.focus();
      return clients.openWindow("/");
    })
  );
});

// ── Lifecycle: skip waiting immediately ─────────────────────────
self.addEventListener("install",  () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(clients.claim()));