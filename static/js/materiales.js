document.addEventListener("DOMContentLoaded", () => {
    const alcance = document.querySelector("[name='alcance']");
    const alumnos = document.querySelector("[data-alumnos]");
    const previewButton = document.querySelector("[data-preview-button]");
    const preview = document.querySelector("[data-preview]");

    function toggleAlumnos() {
        if (!alcance || !alumnos) return;
        alumnos.hidden = alcance.value !== "INDIVIDUAL";
    }

    if (alcance) {
        alcance.addEventListener("change", toggleAlumnos);
        toggleAlumnos();
    }

    if (previewButton && preview) {
        previewButton.addEventListener("click", () => {
            const title = document.querySelector("[name='titulo']").value || "Vista previa";
            const fields = ["introduccion", "objetivo", "metodologia_trabajo", "detalles_material", "referencias_bibliograficas", "conclusion_material"];
            preview.innerHTML = `<h2>${title}</h2>` + fields.map((field) => {
                const label = document.querySelector(`[for='${field}']`).textContent;
                const value = document.querySelector(`[name='${field}']`).value || "Sin contenido";
                return `<section><h3>${label}</h3><p>${value.replaceAll("<", "&lt;")}</p></section>`;
            }).join("");
            preview.hidden = false;
        });
    }
});
