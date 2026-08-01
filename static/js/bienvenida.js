document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".user-card").forEach((card) => {
        card.addEventListener("keyup", (event) => {
            if (event.key === "Enter") card.click();
        });
    });
});
