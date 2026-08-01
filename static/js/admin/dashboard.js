document.addEventListener("DOMContentLoaded", function () {
    const stats = document.querySelectorAll(".stat span");

    stats.forEach(function (stat) {
        const finalValue = Number(stat.textContent.trim());

        if (Number.isNaN(finalValue)) {
            return;
        }

        let currentValue = 0;
        const increment = Math.max(1, Math.ceil(finalValue / 25));

        const timer = setInterval(function () {
            currentValue += increment;

            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }

            stat.textContent = currentValue;
        }, 20);
    });
});