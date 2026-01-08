// Smooth scrolling for anchor links
const menuLinks = document.querySelectorAll('#Menu a[href^="#"]');
menuLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            // Calculate offset to center the section in the viewport
            const rect = target.getBoundingClientRect();
            const scrollY = window.scrollY || window.pageYOffset;
            const viewportHeight = window.innerHeight;
            const sectionHeight = rect.height;
            // Height of the bandeau
            const bandeau = document.getElementById('Bandeau');
            const bandeauHeight = bandeau ? bandeau.offsetHeight : 0;
            // Center the section, but not above the top
            let scrollTo = scrollY + rect.top - ((viewportHeight - sectionHeight) / 2);
            // Prevent scrolling too far up (keep at least the bandeau visible)
            if (scrollTo < bandeauHeight) scrollTo = bandeauHeight;
            window.scrollTo({ top: scrollTo, behavior: 'smooth' });
        }
    });
});

// Collapsible project sections for mobile only
function setupCollapsibleZones() {
    const zones = document.querySelectorAll('.zone > h2');
    function isMobile() {
        return window.innerWidth <= 900;
    }
    zones.forEach(h2 => {
        h2.style.cursor = 'pointer';
        h2.onclick = function () {
            if (isMobile()) {
                const parent = h2.parentElement;
                parent.classList.toggle('collapsed');
            }
        };
    });
    // On resize, expand all if not mobile
    window.addEventListener('resize', () => {
        if (!isMobile()) {
            document.querySelectorAll('.zone.collapsed').forEach(z => z.classList.remove('collapsed'));
        }
    });
}

// Highlight current section in menu
function highlightMenuOnScroll() {
    const sections = document.querySelectorAll('.zone');
    const menuLinks = document.querySelectorAll('#Menu a[href^="#"]');
    window.addEventListener('scroll', () => {
        let current = '';
        let currentSection = null;
        const viewportCenter = window.scrollY + window.innerHeight / 2;
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            const sectionTop = window.scrollY + rect.top;
            const sectionBottom = sectionTop + rect.height;
            if (viewportCenter >= sectionTop && viewportCenter < sectionBottom) {
                current = section.getAttribute('id');
                currentSection = section;
            }
        });
        menuLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
        sections.forEach(section => section.classList.remove('active'));
        if (currentSection) currentSection.classList.add('active');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupCollapsibleZones();
    highlightMenuOnScroll();
});
