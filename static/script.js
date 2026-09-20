document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const button = document.querySelector("button[type='submit']");
    const textarea = document.querySelector("textarea[name='question']");

    if (form && button) {
        form.addEventListener("submit", (e) => {
            if (textarea && textarea.value.trim() === "") {
                e.preventDefault();
                textarea.focus();
                return;
            }

            button.disabled = true;
            button.innerHTML = '<span class="spinner"></span> Consulting AI Tutor...';
            button.style.opacity = "0.9";
            button.style.cursor = "wait";
            form.submit();
        });
    }

    const outputSection = document.querySelector(".output-section");
    if (outputSection) {
        outputSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
});