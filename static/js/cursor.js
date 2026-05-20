/* Custom spotlight cursor — desktop only, respects reduced-motion. */
(function () {
    const isTouch = matchMedia('(hover: none) or (pointer: coarse)').matches;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (isTouch || reduced) return;

    const dot  = document.getElementById('cursorDot');
    const ring = document.getElementById('cursorRing');
    const glow = document.getElementById('cursorGlow');
    if (!dot || !ring || !glow) return;

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX, ringY = mouseY;
    let glowX = mouseX, glowY = mouseY;
    let active = false;

    window.addEventListener('mousemove', function (e) {
        mouseX = e.clientX;
        mouseY = e.clientY;
        if (!active) {
            active = true;
            document.body.classList.add('cursor-active');
        }
    }, { passive: true });

    window.addEventListener('mouseleave', function () {
        active = false;
        document.body.classList.remove('cursor-active');
    });

    const HOVERABLE = 'a, button, label, [role="button"], summary, .check-item, .service-card, .stat-item, .float-btn, .audio-toggle, .social-btn, .hww-stage-card, .hww-phase-card';

    document.addEventListener('mouseover', function (e) {
        if (e.target.closest && e.target.closest(HOVERABLE)) {
            document.body.classList.add('cursor-hover');
        }
    });
    document.addEventListener('mouseout', function (e) {
        if (e.target.closest && e.target.closest(HOVERABLE)) {
            document.body.classList.remove('cursor-hover');
        }
    });

    document.addEventListener('mousedown', function () { document.body.classList.add('cursor-click'); });
    document.addEventListener('mouseup',   function () { document.body.classList.remove('cursor-click'); });

    function tick() {
        dot.style.transform  = `translate(${mouseX}px, ${mouseY}px) translate(-50%, -50%)`;

        ringX += (mouseX - ringX) * 0.22;
        ringY += (mouseY - ringY) * 0.22;
        ring.style.transform = `translate(${ringX}px, ${ringY}px) translate(-50%, -50%)`;

        glowX += (mouseX - glowX) * 0.08;
        glowY += (mouseY - glowY) * 0.08;
        glow.style.transform = `translate(${glowX}px, ${glowY}px) translate(-50%, -50%)`;

        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
})();
