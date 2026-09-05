/* =============================================================
   CAREERAI — MAIN JAVASCRIPT
   Scroll-reveal, animated counters, particles, and interactions
   ============================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("CareerAI Engine loaded successfully.");


    /* ----------------------------------------------------------
       SCROLL REVEAL (IntersectionObserver)
       Any element with [data-reveal] or [data-stagger]
       ---------------------------------------------------------- */

    const revealElements = document.querySelectorAll("[data-reveal], [data-stagger]");

    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("revealed");
                        revealObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );

        revealElements.forEach((el) => revealObserver.observe(el));
    }


    /* ----------------------------------------------------------
       ANIMATED COUNTERS
       Elements with [data-counter="123"] count from 0 → 123
       ---------------------------------------------------------- */

    const counterElements = document.querySelectorAll("[data-counter]");

    if (counterElements.length > 0) {
        const counterObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        counterObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );

        counterElements.forEach((el) => counterObserver.observe(el));
    }

    function animateCounter(el) {
        const target = parseInt(el.getAttribute("data-counter"), 10);
        const suffix = el.getAttribute("data-suffix") || "";
        const prefix = el.getAttribute("data-prefix") || "";
        const duration = 1800;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);

            el.textContent = prefix + current.toLocaleString() + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }


    /* ----------------------------------------------------------
       SCORE RING ANIMATION
       Elements with [data-score] animate conic-gradient
       ---------------------------------------------------------- */

    const scoreRings = document.querySelectorAll("[data-score]");

    if (scoreRings.length > 0) {
        const scoreObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateScore(entry.target);
                        scoreObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );

        scoreRings.forEach((el) => scoreObserver.observe(el));
    }

    function animateScore(el) {
        const target = parseInt(el.getAttribute("data-score"), 10);
        const duration = 1600;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);

            el.style.background =
                "conic-gradient(var(--ring-color, #8b5cf6) " +
                current +
                "%, var(--ring-bg, #1b2740) " +
                current +
                "% 100%)";

            // Update the number display if it exists inside
            const numEl = el.querySelector("[data-score-num]");
            if (numEl) {
                numEl.textContent = current;
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        // Start from 0
        el.style.background =
            "conic-gradient(var(--ring-color, #8b5cf6) 0%, var(--ring-bg, #1b2740) 0% 100%)";

        requestAnimationFrame(update);
    }


    /* ----------------------------------------------------------
       PROGRESS BAR ANIMATION
       Elements with .bar-animated grow width on scroll
       ---------------------------------------------------------- */

    const animatedBars = document.querySelectorAll(".bar-animated");

    if (animatedBars.length > 0) {
        const barObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("revealed");
                        const bar = entry.target.querySelector("span");
                        if (bar) {
                            const targetWidth = bar.getAttribute("data-width");
                            if (targetWidth) {
                                setTimeout(() => {
                                    bar.style.width = targetWidth;
                                }, 100);
                            }
                        }
                        barObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );

        animatedBars.forEach((el) => barObserver.observe(el));
    }


    /* ----------------------------------------------------------
       PARTICLE CANVAS — Hero backgrounds
       ---------------------------------------------------------- */

    const particleCanvas = document.getElementById("particle-canvas");

    if (particleCanvas) {
        initParticles(particleCanvas);
    }

    function initParticles(canvas) {
        const ctx = canvas.getContext("2d");
        let width, height, particles;
        const PARTICLE_COUNT = 55;
        let animFrame;

        function resize() {
            const parent = canvas.parentElement;
            width = canvas.width = parent.offsetWidth;
            height = canvas.height = parent.offsetHeight;
        }

        function createParticles() {
            particles = [];
            for (let i = 0; i < PARTICLE_COUNT; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: Math.random() * 1.8 + 0.5,
                    dx: (Math.random() - 0.5) * 0.35,
                    dy: (Math.random() - 0.5) * 0.35,
                    alpha: Math.random() * 0.4 + 0.1,
                    hue: Math.random() > 0.5 ? 260 : 210,
                });
            }
        }

        function draw() {
            ctx.clearRect(0, 0, width, height);

            for (const p of particles) {
                p.x += p.dx;
                p.y += p.dy;

                if (p.x < 0) p.x = width;
                if (p.x > width) p.x = 0;
                if (p.y < 0) p.y = height;
                if (p.y > height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = `hsla(${p.hue}, 70%, 72%, ${p.alpha})`;
                ctx.fill();
            }

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(167, 139, 250, ${
                            0.06 * (1 - dist / 120)
                        })`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }

            animFrame = requestAnimationFrame(draw);
        }

        resize();
        createParticles();
        draw();

        window.addEventListener("resize", () => {
            resize();
            createParticles();
        });
    }


    /* ----------------------------------------------------------
       UPLOAD DRAG-DROP ENHANCEMENT
       ---------------------------------------------------------- */

    const uploadAreas = document.querySelectorAll(".upload-area-enhanced");

    uploadAreas.forEach((area) => {
        ["dragenter", "dragover"].forEach((evt) => {
            area.addEventListener(evt, (e) => {
                e.preventDefault();
                area.classList.add("drag-over");
            });
        });

        ["dragleave", "drop"].forEach((evt) => {
            area.addEventListener(evt, (e) => {
                e.preventDefault();
                area.classList.remove("drag-over");
            });
        });
    });

    // File input change → confirmation animation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach((input) => {
        input.addEventListener("change", () => {
            const uploadArea = input.closest(".upload-area-enhanced, .upload-area");
            if (uploadArea && input.files.length > 0) {
                uploadArea.classList.add("file-confirmed");
                setTimeout(() => uploadArea.classList.remove("file-confirmed"), 500);
            }
        });
    });


    /* ----------------------------------------------------------
       ANALYZE BUTTON — Loading state on submit
       ---------------------------------------------------------- */

    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
        form.addEventListener("submit", () => {
            const btn = form.querySelector(".analyze-btn, .login-btn, .create-btn");
            if (btn) {
                btn.classList.add("btn-loading");
            }
        });
    });


    /* ----------------------------------------------------------
       COMPANY CARD SELECTION BOUNCE
       ---------------------------------------------------------- */

    const companyInputs = document.querySelectorAll(
        '.company-option input[type="checkbox"], .company-option input[type="radio"]'
    );

    companyInputs.forEach((input) => {
        input.addEventListener("change", () => {
            const card = input.nextElementSibling;
            if (card && input.checked) {
                card.classList.add("selection-bounce");
                setTimeout(() => card.classList.remove("selection-bounce"), 400);
            }
        });
    });


    /* ----------------------------------------------------------
       NAVBAR SCROLL EFFECT (for index page)
       ---------------------------------------------------------- */

    const nav = document.querySelector(".site-nav");
    if (nav) {
        window.addEventListener("scroll", () => {
            nav.classList.toggle("scrolled", window.scrollY > 60);
        });
    }

});