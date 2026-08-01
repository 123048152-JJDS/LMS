document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form.form-grid");

    if (!form || !window.location.pathname.includes("/admin/materias")) {
        return;
    }

    const clave = form.querySelector("input[name='clave']");
    const nombre = form.querySelector("input[name='nombre']");

    if (clave) {
        clave.addEventListener("input", function () {
            clave.value = clave.value.toUpperCase().replace(/\s+/g, "-");
        });
    }

    form.addEventListener("submit", function (event) {
        if (!clave.value.trim() || !nombre.value.trim()) {
            event.preventDefault();
            alert("La clave y el nombre de la materia son obligatorios.");
        }
    });
});