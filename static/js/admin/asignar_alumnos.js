document.addEventListener("DOMContentLoaded", function () {
    if (!window.location.pathname.includes("/alumnos")) {
        return;
    }

    const list = document.querySelector(".check-list");

    if (!list) {
        return;
    }

    const toolbar = document.createElement("div");
    toolbar.className = "form-actions";
    toolbar.innerHTML = `
        <button type="button" class="button secondary" data-check-all>Seleccionar todos</button>
        <button type="button" class="button secondary" data-uncheck-all>Limpiar selección</button>
        <input type="search" placeholder="Buscar alumno..." data-filter class="admin-filter-input">
    `;

    list.before(toolbar);

    const checkAll = toolbar.querySelector("[data-check-all]");
    const uncheckAll = toolbar.querySelector("[data-uncheck-all]");
    const filter = toolbar.querySelector("[data-filter]");

    checkAll.addEventListener("click", function () {
        list.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
            checkbox.checked = true;
        });
    });

    uncheckAll.addEventListener("click", function () {
        list.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
            checkbox.checked = false;
        });
    });

    filter.addEventListener("input", function () {
        const value = filter.value.toLowerCase().trim();

        list.querySelectorAll(".check").forEach(function (item) {
            item.style.display = item.textContent.toLowerCase().includes(value) ? "flex" : "none";
        });
    });
});