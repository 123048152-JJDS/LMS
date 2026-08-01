document.addEventListener("DOMContentLoaded", function () {
    const table = document.querySelector(".table-wrap table");

    if (!table || !window.location.pathname.includes("/admin/usuarios")) {
        return;
    }

    const search = document.createElement("div");
    search.className = "admin-search";
    search.innerHTML = `
        <input type="search" placeholder="Buscar usuario, correo o identificador...">
    `;

    table.closest(".table-wrap").before(search);

    const input = search.querySelector("input");
    const rows = table.querySelectorAll("tbody tr");

    input.addEventListener("input", function () {
        const value = input.value.toLowerCase().trim();

        rows.forEach(function (row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(value) ? "" : "none";
        });
    });

    document.querySelectorAll("form[onsubmit]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmed = confirm("¿Confirmas esta acción?");
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});