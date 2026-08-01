document.addEventListener("DOMContentLoaded", function () {
    const table = document.querySelector(".table-wrap table");

    if (!table || !window.location.pathname.includes("/admin/clases")) {
        return;
    }

    const search = document.createElement("div");
    search.className = "admin-search";
    search.innerHTML = `
        <input type="search" placeholder="Buscar clase, materia, periodo o grupo...">
    `;

    table.closest(".table-wrap").before(search);

    const input = search.querySelector("input");
    const rows = table.querySelectorAll("tbody tr");

    input.addEventListener("input", function () {
        const value = input.value.toLowerCase().trim();

        rows.forEach(function (row) {
            row.style.display = row.textContent.toLowerCase().includes(value) ? "" : "none";
        });
    });
});