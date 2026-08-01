document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("adminSidebar");
    const toggle = document.getElementById("sidebarToggle");
    const links = document.querySelectorAll(".sidebar-link");
    const currentPath = window.location.pathname;

    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });
    }

    links.forEach(function (link) {
        const href = link.getAttribute("href");

        if (href && currentPath.startsWith(href)) {
            link.classList.add("active");
        }
    });

    document.querySelectorAll(".flash-message").forEach(function (message) {
        setTimeout(function () {
            message.style.opacity = "0";
            message.style.transform = "translateY(-8px)";

            setTimeout(function () {
                message.remove();
            }, 300);
        }, 4500);
    });
});