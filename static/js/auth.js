// ===== JWT AUTHENTICATION MODULE =====
// Handles JWT auth via HTTP-only cookies (set by backend)

const Auth = {
  user: null,

  // ── Login ──
  async login(identifier, password) {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username: identifier, password }),
      });
      const data = await res.json();
      if (data.success) {
        this.user = data.data.user;
        return { success: true, user: this.user, message: data.message };
      }
      return { success: false, message: data.message || 'Login failed', errors: data.errors };
    } catch (err) {
      return { success: false, message: 'Network error. Please try again.' };
    }
  },

  // ── Register ──
  async register(username, email, password, confirmPassword) {
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, email, password, confirmPassword }),
      });
      const data = await res.json();
      if (data.success) {
        this.user = data.data.user;
        return { success: true, user: this.user, message: data.message };
      }
      return { success: false, message: data.message || 'Registration failed', errors: data.errors };
    } catch (err) {
      return { success: false, message: 'Network error. Please try again.' };
    }
  },

  // ── Logout ──
  async logout() {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'same-origin',
      });
    } catch (e) {
      // Ignore — we clear local state regardless
    }
    this.user = null;
    window.location.href = '/login/';
  },

  // ── Refresh tokens ──
  async refresh() {
    try {
      const res = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        credentials: 'same-origin',
      });
      if (!res.ok) {
        // Refresh failed — session expired
        this.user = null;
        return false;
      }
      return true;
    } catch (e) {
      return false;
    }
  },

  // ── Get current user from API ──
  async fetchUser() {
    try {
      const res = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          this.user = data.data;
          return this.user;
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  },

  // ── Get user from memory ──
  getUser() {
    return this.user;
  },

  // ── User display helpers ──
  getUserInitials() {
    const user = this.getUser();
    if (!user) return 'U';
    if (user.firstName && user.lastName) {
      return (user.firstName[0] + user.lastName[0]).toUpperCase();
    }
    return user.username ? user.username[0].toUpperCase() : 'U';
  },

  getUserDisplayName() {
    const user = this.getUser();
    if (!user) return 'User';
    if (user.firstName) return user.firstName;
    return user.username || 'User';
  },

  isLoggedIn() {
    return !!this.getUser();
  },

  // ── Change password ──
  async changePassword(currentPassword, newPassword, confirmPassword) {
    try {
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ currentPassword, newPassword, confirmPassword }),
      });
      const data = await res.json();
      return { success: data.success, message: data.message, errors: data.errors };
    } catch (err) {
      return { success: false, message: 'Network error. Please try again.' };
    }
  },

  // ── Auto-refresh (every 12 min for 15-min access tokens) ──
  startAutoRefresh() {
    this._refreshInterval = setInterval(() => this.refresh(), 12 * 60 * 1000);
  },

  stopAutoRefresh() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  },

  // ── Initialize on protected pages ──
  async init() {
    const user = this.getUser();
    if (user) {
      this.startAutoRefresh();
      // Silently refresh user data from API
      this.fetchUser();
    }
    return user;
  },
};
