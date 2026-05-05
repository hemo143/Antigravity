/* ══════════════════════════════════════════════
   ProAV Solutions — Landing Page JS
══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    const isAr = window.LANG === 'ar';

    // ── AOS Init ──────────────────────────────
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, easing: 'ease-out-cubic', once: true, offset: 60 });
    }

    // ── Sticky Navbar ─────────────────────────
    const navbar = document.getElementById('mainNav');
    if (navbar) {
        window.addEventListener('scroll', function () {
            navbar.classList.toggle('scrolled', window.scrollY > 60);
        }, { passive: true });
    }

    // ── Mobile Menu Toggle ────────────────────
    const toggle    = document.getElementById('navToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    if (toggle && mobileMenu) {
        toggle.addEventListener('click', function () {
            mobileMenu.classList.toggle('open');
        });
        mobileMenu.querySelectorAll('.mobile-link, .btn-quote').forEach(function (link) {
            link.addEventListener('click', function () { mobileMenu.classList.remove('open'); });
        });
    }

    // ── Smooth Scroll ─────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                const top = target.getBoundingClientRect().top + window.scrollY - 80;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        });
    });

    // ── Portfolio Filter ──────────────────────
    const filterBtns    = document.querySelectorAll('.pf-btn');
    const portfolioCards = document.querySelectorAll('.portfolio-card');

    filterBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const filter = this.dataset.filter;
            filterBtns.forEach(function (b) { b.classList.remove('active'); });
            this.classList.add('active');

            portfolioCards.forEach(function (card) {
                if (filter === 'all' || card.dataset.type === filter) {
                    card.style.display = 'block';
                    card.style.opacity = '0';
                    setTimeout(function () {
                        card.style.transition = 'opacity 0.4s';
                        card.style.opacity    = '1';
                    }, 10);
                } else {
                    card.style.transition = 'opacity 0.3s';
                    card.style.opacity    = '0';
                    setTimeout(function () { card.style.display = 'none'; }, 300);
                }
            });
        });
    });

    // ── Quote Form — real AJAX submission ─────
    const quoteForm  = document.getElementById('quoteForm');
    const formSuccess = document.getElementById('formSuccess');
    const submitBtn   = document.getElementById('submitBtn');

    if (quoteForm && formSuccess && submitBtn) {
        const originalBtnHTML = submitBtn.innerHTML;

        quoteForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // Loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = isAr
                ? '<span class="spinner-border spinner-border-sm me-2"></span>جاري الإرسال...'
                : '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';

            const formData = new FormData(quoteForm);

            fetch(quoteForm.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
            })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.success) {
                    quoteForm.reset();
                    formSuccess.classList.remove('d-none');
                    quoteForm.querySelectorAll('input,select,textarea,button[type=submit]').forEach(function (el) {
                        el.style.display = 'none';
                    });
                } else {
                    alert(isAr ? 'حدث خطأ، يرجى المحاولة مجدداً.' : 'An error occurred. Please try again.');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHTML;
                }
            })
            .catch(function () {
                alert(isAr ? 'حدث خطأ في الاتصال، يرجى المحاولة مجدداً.' : 'Connection error. Please try again.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHTML;
            });
        });
    }

    // ── Active nav link on scroll ─────────────
    const sections   = document.querySelectorAll('section[id]');
    const navAnchors = document.querySelectorAll('.nav-links a');

    if (sections.length && navAnchors.length) {
        window.addEventListener('scroll', function () {
            let current = '';
            sections.forEach(function (s) {
                if (window.scrollY >= s.offsetTop - 120) current = s.id;
            });
            navAnchors.forEach(function (a) {
                a.classList.toggle('active', a.getAttribute('href') === '#' + current);
            });
        }, { passive: true });
    }

    // ── Counter animation (hero stats) ────────
    function animateCounter(el, target, duration) {
        let start = 0;
        const step = target / (duration / 16);
        const suffix = el.textContent.replace(/[0-9]/g, '');
        const timer = setInterval(function () {
            start += step;
            if (start >= target) {
                el.textContent = target + suffix;
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(start) + suffix;
            }
        }, 16);
    }

    const statsSection = document.querySelector('.hero-stats');
    if (statsSection) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    document.querySelectorAll('.stat-num').forEach(function (el) {
                        const num = parseInt(el.textContent.replace(/[^0-9]/g, ''));
                        animateCounter(el, num, 1200);
                    });
                    observer.disconnect();
                }
            });
        }, { threshold: 0.5 });
        observer.observe(statsSection);
    }

});
