/* ═══════════════════════════════════════════════════════════════
   EventPro - Main JavaScript
════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ─── Sidebar Toggle (Mobile) ─────────────────────────────────
    const sidebar = document.getElementById('sidebar');
    const mainWrapper = document.getElementById('mainWrapper');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');

            // Add/remove overlay
            let overlay = document.querySelector('.sidebar-overlay');
            if (sidebar.classList.contains('open')) {
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.className = 'sidebar-overlay';
                    document.body.appendChild(overlay);
                }
                overlay.addEventListener('click', closeSidebar);
            } else {
                removeSidebarOverlay();
            }
        });
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        removeSidebarOverlay();
    }

    function removeSidebarOverlay() {
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) overlay.remove();
    }

    // ─── Auto-dismiss Alerts ─────────────────────────────────────
    setTimeout(function () {
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // ─── Active Nav Link ─────────────────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ─── Confirm Delete ──────────────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });

    // ─── Slug Auto-generator ─────────────────────────────────────
    const nameInput = document.querySelector('[name="name"]');
    const slugInput = document.querySelector('[name="slug"]');

    if (nameInput && slugInput && !slugInput.value) {
        nameInput.addEventListener('input', function () {
            slugInput.value = this.value
                .toLowerCase()
                .replace(/[^a-z0-9\s-]/g, '')
                .replace(/\s+/g, '-')
                .replace(/-+/g, '-')
                .replace(/^-|-$/g, '');
        });
    }

    // ─── Tooltip Initialization ──────────────────────────────────
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    // ─── Animate Stat Cards on Load ──────────────────────────────
    document.querySelectorAll('.stat-card').forEach(function (card, i) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(function () {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, i * 80);
    });

    // ─── Counter Animation ────────────────────────────────────────
    document.querySelectorAll('.stat-card-value').forEach(function (el) {
        const target = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10);
        if (!isNaN(target) && target > 0) {
            let current = 0;
            const step = Math.max(1, Math.floor(target / 30));
            const timer = setInterval(function () {
                current = Math.min(current + step, target);
                el.textContent = current.toLocaleString();
                if (current >= target) clearInterval(timer);
            }, 30);
        }
    });

    // ─── Form Validation Feedback ─────────────────────────────────
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const original = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                // Re-enable after 5s as fallback
                setTimeout(function () {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = original;
                }, 5000);
            }
        });
    });

});
