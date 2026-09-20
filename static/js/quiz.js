// ==========================================================================
// Virtual AI Tutor - Interactive Quiz Runner Engine
// ==========================================================================

let currentStep = 1;
const answers = {};

document.addEventListener("DOMContentLoaded", () => {
    const btnNext = document.getElementById("btnNextQ");
    const btnPrev = document.getElementById("btnPrevQ");
    const btnSubmit = document.getElementById("btnSubmitQuiz");

    // Option Selection Styling
    document.querySelectorAll(".option-label").forEach((label) => {
        label.addEventListener("click", () => {
            const container = label.closest(".options-container");
            container.querySelectorAll(".option-label").forEach((l) => l.classList.remove("selected"));
            label.classList.add("selected");

            const radio = label.querySelector(".option-radio");
            if (radio) {
                radio.checked = true;
                const stepCard = label.closest(".question-step-card");
                const qId = stepCard.getAttribute("data-question-id");
                answers[qId] = radio.value;
            }
        });
    });

    // Next Step
    if (btnNext) {
        btnNext.addEventListener("click", () => {
            if (currentStep < TOTAL_QUESTIONS) {
                goToStep(currentStep + 1);
            }
        });
    }

    // Prev Step
    if (btnPrev) {
        btnPrev.addEventListener("click", () => {
            if (currentStep > 1) {
                goToStep(currentStep - 1);
            }
        });
    }

    // Submit Quiz
    if (btnSubmit) {
        btnSubmit.addEventListener("click", () => {
            submitQuizAnswers();
        });
    }

    // Start Timer (10 minutes countdown)
    startQuizTimer(10 * 60);
    updateProgressUI();
});

function goToStep(step) {
    document.querySelectorAll(".question-step-card").forEach((c) => {
        c.style.display = "none";
        c.classList.remove("active");
    });

    const target = document.getElementById(`qStep_${step}`);
    if (target) {
        target.style.display = "block";
        target.classList.add("active");
        currentStep = step;
        updateProgressUI();
    }
}

function updateProgressUI() {
    const fill = document.getElementById("quizProgressFill");
    const numSpan = document.getElementById("currentQuestionNum");
    const btnPrev = document.getElementById("btnPrevQ");
    const btnNext = document.getElementById("btnNextQ");
    const btnSubmit = document.getElementById("btnSubmitQuiz");

    const pct = Math.round((currentStep / TOTAL_QUESTIONS) * 100);
    if (fill) fill.style.width = pct + "%";
    if (numSpan) numSpan.textContent = currentStep;

    if (btnPrev) btnPrev.disabled = currentStep === 1;

    if (currentStep === TOTAL_QUESTIONS) {
        if (btnNext) btnNext.style.display = "none";
        if (btnSubmit) btnSubmit.style.display = "inline-flex";
    } else {
        if (btnNext) btnNext.style.display = "inline-flex";
        if (btnSubmit) btnSubmit.style.display = "none";
    }
}

function startQuizTimer(durationSeconds) {
    const timerElem = document.getElementById("timerText");
    let remaining = durationSeconds;

    const interval = setInterval(() => {
        if (remaining <= 0) {
            clearInterval(interval);
            if (timerElem) timerElem.textContent = "00:00";
            alert("Time limit reached! Submitting quiz answers automatically...");
            submitQuizAnswers();
            return;
        }

        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        if (timerElem) {
            timerElem.textContent = `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
        }
        remaining--;
    }, 1000);
}

async function submitQuizAnswers() {
    const btnSubmit = document.getElementById("btnSubmitQuiz");
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Scoring your answers...";
    }

    try {
        const response = await fetch(SUBMIT_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answers: answers }),
        });

        const data = await response.json();
        if (data.success) {
            window.location.href = BASE_RESULT_URL + data.result.attempt_id;
        } else {
            alert("Submission error: " + (data.error || "Please try again."));
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = "Submit Quiz for Scoring";
            }
        }
    } catch (err) {
        console.error("Quiz submission error:", err);
        alert("Failed to submit quiz. Please check network connection.");
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.textContent = "Submit Quiz for Scoring";
        }
    }
}
