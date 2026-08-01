document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form.form-grid");

    if (!form || !window.location.pathname.includes("/admin/clases")) {
        return;
    }

    const codigo = form.querySelector("input[name='codigo_clase']");
    const grupo = form.querySelector("input[name='nombre_grupo']");
    const materia = form.querySelector("select[name='materia_id']");
    const periodo = form.querySelector("select[name='periodo_id']");

    function normalizar(value) {
        return value
            .trim()
            .toUpperCase()
            .replace(/\s+/g, "-")
            .replace(/[^A-Z0-9-]/g, "");
    }

    if (grupo) {
        grupo.addEventListener("input", function () {
            grupo.value = normalizar(grupo.value);
        });
    }

    if (codigo) {
        codigo.addEventListener("input", function () {
            codigo.value = normalizar(codigo.value);
        });
    }

    form.addEventListener("submit", function (event) {
        if (!materia.value || !periodo.value || !grupo.value.trim()) {
            event.preventDefault();
            alert("Selecciona materia, periodo y grupo.");
        }
    });
});