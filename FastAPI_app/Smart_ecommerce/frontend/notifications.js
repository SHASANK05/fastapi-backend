const API_BASE_URL = "http://127.0.0.1:8000";
let badgeInterval = null;

// Read auth token from localStorage automatically
function getAuthHeaders() {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

// 1. Update unread badge counter
async function updateNotificationBadge() {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token");
  if (!token) {
    stopNotificationPolling();
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
      headers: getAuthHeaders()
    });

    if (res.status === 401) {
      console.warn("Token expired. Stopping polling.");
      stopNotificationPolling();
      const badge = document.getElementById("notification-badge");
      if (badge) badge.style.display = "none";
      return;
    }

    if (!res.ok) return;

    const data = await res.json();
    const badge = document.getElementById("notification-badge");

    if (badge) {
      if (data.unread_count > 0) {
        badge.innerText = data.unread_count;
        badge.style.display = "inline-block";
      } else {
        badge.style.display = "none";
      }
    }
  } catch (err) {
    console.error("Failed to load badge count:", err);
  }
}

// 2. Fetch notifications list into the dropdown
async function fetchNotifications() {
  const container = document.getElementById("notification-list");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE_URL}/notifications?unread_only=false`, {
      headers: getAuthHeaders()
    });

    if (res.status === 401) {
      container.innerHTML = `<p style="font-size: 12px; color: #e53e3e; text-align: center;">Session expired. Please log in again.</p>`;
      stopNotificationPolling();
      return;
    }

    if (!res.ok) {
      container.innerHTML = `<p style="font-size: 12px; color: #e53e3e; text-align: center;">Failed to load notifications.</p>`;
      return;
    }

    const notifications = await res.json();
    if (notifications.length === 0) {
      container.innerHTML = `<p style="font-size: 12px; color: #a0aec0; text-align: center; margin: 12px 0;">No notifications found.</p>`;
      return;
    }

    container.innerHTML = notifications.map(item => `
      <div class="notif-item ${item.is_read ? 'read' : 'unread'}" onclick="markSingleRead(${item.id})" style="padding: 10px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 8px; transition: all 0.2s ease; background-color: ${item.is_read ? '#ffffff' : '#ebf8ff'}; border: 1px solid ${item.is_read ? '#edf2f7' : '#bee3f8'};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 11px; font-weight: bold; color: ${item.is_read ? '#718096' : '#2b6cb0'};">
            ${item.notification_type || "Notification"}
          </span>
          <span style="font-size: 10px; color: #a0aec0;">
            ${item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
          </span>
        </div>
        <div style="font-size: 12px; color: #2d3748; margin-top: 4px; line-height: 1.4;">
          ${item.message}
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p style="font-size: 12px; color: #e53e3e; text-align: center;">Network error connecting to API.</p>`;
  }
}

// 3. Mark single notification as read
async function markSingleRead(id) {
  try {
    await fetch(`${API_BASE_URL}/notifications/${id}/read`, {
      method: "PATCH",
      headers: getAuthHeaders()
    });
    await updateNotificationBadge();
    await fetchNotifications();
  } catch (err) {
    console.error("Failed to mark read:", err);
  }
}

// 4. Mark all as read
async function markAllNotificationsRead() {
  try {
    await fetch(`${API_BASE_URL}/notifications/read-all`, {
      method: "PATCH",
      headers: getAuthHeaders()
    });
    await updateNotificationBadge();
    await fetchNotifications();
  } catch (err) {
    console.error("Failed to mark all read:", err);
  }
}

// 5. Dropdown toggle
function toggleNotificationDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("notification-dropdown");
  if (!dropdown) return;

  const isVisible = dropdown.style.display === "block";
  if (isVisible) {
    dropdown.style.display = "none";
  } else {
    dropdown.style.display = "block";
    fetchNotifications();
  }
}

// Close dropdown on outside click
document.addEventListener("click", (e) => {
  const container = document.querySelector(".notification-container");
  const dropdown = document.getElementById("notification-dropdown");
  if (container && dropdown && !container.contains(e.target)) {
    dropdown.style.display = "none";
  }
});

function startNotificationPolling() {
  stopNotificationPolling();
  updateNotificationBadge();
  badgeInterval = setInterval(updateNotificationBadge, 30000);
}

function stopNotificationPolling() {
  if (badgeInterval) {
    clearInterval(badgeInterval);
    badgeInterval = null;
  }
}

// Auto-start on page load
document.addEventListener("DOMContentLoaded", () => {
  startNotificationPolling();
});