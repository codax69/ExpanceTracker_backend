// ===== EXPENSE TRACKER - SHARED APP JS =====

// --- Theme ---
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  if (saved === 'light') document.body.classList.add('light-mode');
  updateThemeIcon();
}
function toggleTheme() {
  document.body.classList.toggle('light-mode');
  localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
  updateThemeIcon();
  if (typeof updateChartsTheme === 'function') updateChartsTheme();
}
function updateThemeIcon() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const isLight = document.body.classList.contains('light-mode');
  btn.innerHTML = isLight
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
}

// --- Sidebar ---
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const collapseBtn = document.getElementById('collapseBtn');
  const menuBtn = document.getElementById('menuBtn');
  if (collapseBtn) {
    collapseBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
  }
  if (menuBtn) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
  // Close sidebar on mobile when clicking outside
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 1024 && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuBtn) {
      sidebar.classList.remove('open');
    }
  });
  // Restore state
  if (localStorage.getItem('sidebarCollapsed') === 'true' && window.innerWidth > 1024) {
    sidebar.classList.add('collapsed');
  }
  // Set active nav
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('href') === page) item.classList.add('active');
  });
  document.querySelectorAll('.bottom-nav-item').forEach(item => {
    if (item.getAttribute('href') === page) item.classList.add('active');
  });
}

// --- Animated Counter ---
function animateCounter(el, target, prefix = '', suffix = '', duration = 1200) {
  let start = 0;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = prefix + Math.floor(target * eased).toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// --- Toast ---
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) { container = document.createElement('div'); container.className = 'toast-container'; document.body.appendChild(container); }
  const icons = {
    success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
    error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
    warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01"/></svg>'
  };
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = (icons[type] || icons.success) + `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 3500);
}

// --- Modal ---
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

// --- Toggle ---
function initToggles() {
  document.querySelectorAll('.toggle').forEach(t => {
    t.addEventListener('click', () => t.classList.toggle('active'));
  });
}

// --- Currency Format ---
function formatCurrency(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 0 });
}

// --- Sample Data Store ---
const AppData = {
  expenses: [
    { id: 1, title: 'Grocery Shopping', amount: 142, category: 'Food', method: 'Credit Card', date: '2026-05-07', status: 'completed' },
    { id: 2, title: 'Netflix Subscription', amount: 15, category: 'Entertainment', method: 'Debit Card', date: '2026-05-06', status: 'completed' },
    { id: 3, title: 'Electricity Bill', amount: 89, category: 'Utilities', method: 'Bank Transfer', date: '2026-05-05', status: 'pending' },
    { id: 4, title: 'Gym Membership', amount: 50, category: 'Health', method: 'Credit Card', date: '2026-05-04', status: 'completed' },
    { id: 5, title: 'Coffee & Snacks', amount: 24, category: 'Food', method: 'Cash', date: '2026-05-03', status: 'completed' },
    { id: 6, title: 'Uber Rides', amount: 37, category: 'Transport', method: 'Debit Card', date: '2026-05-02', status: 'completed' },
    { id: 7, title: 'Office Supplies', amount: 63, category: 'Shopping', method: 'Credit Card', date: '2026-05-01', status: 'completed' },
    { id: 8, title: 'Internet Bill', amount: 75, category: 'Utilities', method: 'Auto Pay', date: '2026-04-30', status: 'completed' },
    { id: 9, title: 'Restaurant Dinner', amount: 86, category: 'Food', method: 'Credit Card', date: '2026-04-29', status: 'completed' },
    { id: 10, title: 'Spotify Premium', amount: 10, category: 'Entertainment', method: 'Debit Card', date: '2026-04-28', status: 'completed' },
  ],
  income: [
    { id: 1, source: 'Salary', amount: 5200, date: '2026-05-01', method: 'Bank Transfer', desc: 'Monthly salary' },
    { id: 2, source: 'Freelance', amount: 1200, date: '2026-05-03', method: 'PayPal', desc: 'Web design project' },
    { id: 3, source: 'Dividends', amount: 340, date: '2026-04-28', method: 'Brokerage', desc: 'Q1 dividends' },
    { id: 4, source: 'Side Project', amount: 450, date: '2026-04-20', method: 'Stripe', desc: 'App subscription revenue' },
  ],
  categories: [
    { name: 'Food', icon: '🍔', color: '#10b981', budget: 500, spent: 252 },
    { name: 'Transport', icon: '🚗', color: '#06b6d4', budget: 200, spent: 37 },
    { name: 'Entertainment', icon: '🎬', color: '#8b5cf6', budget: 150, spent: 25 },
    { name: 'Utilities', icon: '⚡', color: '#f59e0b', budget: 300, spent: 164 },
    { name: 'Health', icon: '💪', color: '#ef4444', budget: 100, spent: 50 },
    { name: 'Shopping', icon: '🛍️', color: '#ec4899', budget: 250, spent: 63 },
  ]
};

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebar();
  initToggles();
});
