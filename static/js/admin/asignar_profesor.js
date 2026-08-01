document.addEventListener("DOMContentLoaded", function () {
    if (!window.location.pathname.includes("/profesores")) {
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
    `;

    list.before(toolbar);

    toolbar.querySelector("[data-check-all]").addEventListener("click", function () {
        list.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
            checkbox.checked = true;
        });
    });

    toolbar.querySelector("[data-uncheck-all]").addEventListener("click", function () {
        list.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
            checkbox.checked = false;
        });
    });
});