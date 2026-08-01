document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form.form-grid");

    if (!form || !window.location.pathname.includes("/admin/usuarios")) {
        return;
    }

    const nombre = form.querySelector("input[name='nombre']");
    const paterno = form.querySelector("input[name='apellido_paterno']");
    const correo = form.querySelector("input[name='correo']");
    const password = form.querySelector("input[name='password']");

    if (password) {
        const hint = document.createElement("p");
        hint.className = "password-hint";
        hint.textContent = "Para editar un usuario, deja la contraseña vacía si no deseas cambiarla.";
        password.insertAdjacentElement("afterend", hint);
    }

    form.addEventListener("submit", function (event) {
        if (!nombre.value.trim() || !paterno.value.trim() || !correo.value.trim()) {
            event.preventDefault();
            alert("Completa los campos obligatorios.");
            return;
        }

        if (!correo.value.includes("@")) {
            event.preventDefault();
            alert("Ingresa un correo válido.");
        }
    });
});