document.addEventListener("DOMContentLoaded", async () => {
  const popup = document.getElementById("registration-popup");
  const testContainer = document.getElementById("test-container");
  const registrationForm = document.getElementById("registration-form");
  const submitTestBtn = document.getElementById("submit-test-btn");
  const answersUrlInput = document.getElementById("answers_url");
  let timerInterval;
  let timeLeft = 3600; // 60 minutes in seconds
  let currentQuestion = 0;
  let answers = {};

  // Load questions from JSON dynamically
  let questions = [];
  try {
    const response = await fetch("questions.json");
    if (!response.ok) throw new Error("Failed to fetch questions.json");
    questions = await response.json();
    if (!questions.length)
      throw new Error("No questions found in questions.json");
  } catch (e) {
    console.error("Error loading questions:", e);
    document.getElementById("question-text").textContent =
      "Error loading questions. Contact support.";
    return; // Stop execution if questions fail to load
  }

  // Configure Uploadcare
  uploadcare.registerTab("file", uploadcare.files);
  uploadcare.defaults.pubkey = "52a1bfb4563c9c1f7cfd"; // Replace with your Uploadcare public key
  uploadcare.defaults.multiple = false;

  // Show popup on load
  popup.classList.remove("hidden");

  // Handle form submission (local storage)
  registrationForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(registrationForm);
    const studentInfo = Object.fromEntries(formData);
    sessionStorage.setItem("studentInfo", JSON.stringify(studentInfo));
    popup.classList.add("hidden");
    testContainer.classList.remove("hidden");
    startTimer();
    loadQuestion();
  });

  // Start timer
  function startTimer() {
    timerInterval = setInterval(() => {
      timeLeft--;
      const minutes = Math.floor(timeLeft / 60);
      const seconds = timeLeft % 60;
      document.getElementById("timer").textContent = `Time Remaining: ${String(
        minutes
      ).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
      if (timeLeft <= 0) {
        clearInterval(timerInterval);
        alert("Time is up! Submitting your test...");
        submitTest();
      }
    }, 1000);
  }

  // Load question with smooth transition
  function loadQuestion() {
    if (currentQuestion >= questions.length) {
      document.getElementById("question-section").classList.add("hidden");
      document.getElementById("navigation").classList.add("hidden");
      return;
    }
    const questionSection = document.getElementById("question-section");
    questionSection.style.opacity = "0";
    setTimeout(() => {
      document.getElementById("question-text").textContent =
        questions[currentQuestion]?.question || "Loading question...";
      document.querySelectorAll(".option").forEach((option) => {
        const value = option.getAttribute("data-value");
        option.textContent =
          questions[currentQuestion]?.options[value] || value; // Display actual option text
        option.classList.remove("selected");
        if (
          answers[currentQuestion] &&
          answers[currentQuestion].selected_option === value
        ) {
          option.classList.add("selected");
        }
      });
      questionSection.style.opacity = "1";
    }, 300);
  }

  // Handle option selection
  document.querySelectorAll(".option").forEach((option) => {
    option.addEventListener("click", () => {
      answers[currentQuestion] = {
        id: questions[currentQuestion]?.id,
        selected_option: option.getAttribute("data-value"),
      };
      document
        .querySelectorAll(".option")
        .forEach((o) => o.classList.remove("selected"));
      option.classList.add("selected");
    });
  });

  // Navigation
  document.getElementById("prev-btn").addEventListener("click", () => {
    if (currentQuestion > 0) {
      currentQuestion--;
      loadQuestion();
    }
  });

  document.getElementById("next-btn").addEventListener("click", () => {
    if (currentQuestion < questions.length - 1) {
      currentQuestion++;
      loadQuestion();
    }
  });

  // Submit test with Uploadcare and Formsubmit
  submitTestBtn.addEventListener("click", () => {
    clearInterval(timerInterval);
    const studentInfo = JSON.parse(
      sessionStorage.getItem("studentInfo") || "{}"
    );
    const answersBlob = new Blob(
      [
        JSON.stringify(
          {
            student_id: studentInfo.phone || Date.now(),
            answers: Object.values(answers),
          },
          null,
          2
        ),
      ],
      { type: "application/json" }
    );
    const answersFile = new File(
      [answersBlob],
      `student_answers_${Date.now()}.json`
    );

    const uploadcareWidget = uploadcare.Widget("[name=answers_url]");
    uploadcareWidget.openDialog().done((file) => {
      file
        .done((uploadedFile) => {
          const cdnUrl = uploadedFile.cdnUrl;

          // Update hidden input with CDN URL
          answersUrlInput.value = cdnUrl;

          // Update form action to Formsubmit endpoint
          registrationForm.action =
            "https://formsubmit.co/abdulahadchachar92@gmail.com";
          registrationForm.method = "POST";

          // Submit form to Formsubmit
          fetch(registrationForm.action, {
            method: "POST",
            body: new FormData(registrationForm),
            headers: { Accept: "application/json" },
          })
            .then((response) => {
              if (response.ok) {
                document.getElementById("results").classList.remove("hidden");
                document.getElementById(
                  "result-text"
                ).textContent = `Thank you, ${studentInfo.name}! Your report will be shared soon via WhatsApp.`;
                document
                  .getElementById("question-section")
                  .classList.add("hidden");
                document.getElementById("navigation").classList.add("hidden");
                submitTestBtn.classList.add("hidden");
              } else {
                alert(
                  "Submission failed. Please email your answers to abdulahadchachar92@gmail.com."
                );
              }
            })
            .catch((error) => {
              alert(
                "An error occurred. Please try again or email abdulahadchachar92@gmail.com."
              );
            });
        })
        .fail((error) => {
          alert(
            "File upload failed. Please email your answers to abdulahadchachar92@gmail.com."
          );
        });
    });
  });
});
