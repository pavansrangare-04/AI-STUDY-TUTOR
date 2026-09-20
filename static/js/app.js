// ==========================================================================
// Global Application Utilities (Theme, Mobile Sidebar, Flash Auto-dismiss)
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // 1. Theme Management (Dark / Light with LocalStorage Persistence)
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const htmlElement = document.documentElement;

    const savedTheme = localStorage.getItem("ai_tutor_theme") || "dark";
    htmlElement.setAttribute("data-theme", savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const current = htmlElement.getAttribute("data-theme");
            const newTheme = current === "dark" ? "light" : "dark";
            htmlElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("ai_tutor_theme", newTheme);
        });
    }

    // 2. Mobile Sidebar Drawer
    const sidebar = document.getElementById("appSidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }

    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener("click", () => {
            sidebar.classList.remove("open");
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains("open")) {
            if (!sidebar.contains(e.target) && !sidebarToggleBtn.contains(e.target)) {
                sidebar.classList.remove("open");
            }
        }
    });

    // 3. Highlight.js automatic code block initialization
    if (window.hljs) {
        document.querySelectorAll("pre code").forEach((el) => {
            hljs.highlightElement(el);
        });
    }
});
