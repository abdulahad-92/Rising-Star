document.addEventListener("DOMContentLoaded", async () => {
  const popup = document.getElementById("registration-popup");
  const testContainer = document.getElementById("test-container");
  const registrationForm = document.getElementById("registration-form");
  const submitTestBtn = document.getElementById("submit-test-btn");
  const answersUrlInput = document.getElementById("answers_url");
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");
  const questionCounter = document.getElementById("question-counter");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");
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
    return;
  }

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

  // Load question with smooth transition and counter
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
          questions[currentQuestion]?.options[value] || value;
        option.classList.remove("selected");
        if (
          answers[currentQuestion] &&
          answers[currentQuestion].selected_option === value
        ) {
          option.classList.add("selected");
        }
      });
      questionCounter.textContent = `Question ${currentQuestion + 1} of ${
        questions.length
      }`;
      updateButtonStates();
      questionSection.style.opacity = "1";
    }, 300);
  }

  // Update button states based on current question
  function updateButtonStates() {
    if (currentQuestion === 0) {
      prevBtn.classList.add("disabled");
      prevBtn.disabled = true;
    } else {
      prevBtn.classList.remove("disabled");
      prevBtn.disabled = false;
    }
    if (currentQuestion === questions.length - 1) {
      nextBtn.classList.add("disabled");
      nextBtn.disabled = true;
      submitTestBtn.classList.remove("hidden");
    } else {
      nextBtn.classList.remove("disabled");
      nextBtn.disabled = false;
      submitTestBtn.classList.add("hidden");
    }
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
  prevBtn.addEventListener("click", () => {
    if (currentQuestion > 0) {
      currentQuestion--;
      loadQuestion();
    }
  });

  nextBtn.addEventListener("click", () => {
    if (currentQuestion < questions.length - 1) {
      currentQuestion++;
      loadQuestion();
    }
  });

  // Submit test with file download
  submitTestBtn.addEventListener("click", async () => {
    clearInterval(timerInterval);
    loading.classList.remove("hidden");
    submitTestBtn.classList.add("hidden");

    const studentInfo = JSON.parse(
      sessionStorage.getItem("studentInfo") || "{}"
    );
    const answersArray = [];

    // Populate answers, marking skipped questions
    for (let i = 0; i < questions.length; i++) {
      if (answers[i] && answers[i].selected_option) {
        answersArray.push({
          id: questions[i].id,
          selected_option: answers[i].selected_option,
          correctness: answers[i].correctness || "pending", // Placeholder if not pre-assigned
        });
      } else {
        answersArray.push({
          id: questions[i].id,
          selected_option: "skipped",
          correctness: "not attempted",
        });
      }
    }

    const answersBlob = new Blob(
      [
        JSON.stringify(
          {
            student_id: studentInfo.phone || Date.now(),
            answers: answersArray,
          },
          null,
          2
        ),
      ],
      { type: "application/json" }
    );

    const timestamp = new Date()
      .toISOString()
      .replace(/[-:]/g, "")
      .slice(0, 15);
    const filename = `student_answers_${timestamp}.json`;
    const url = window.URL.createObjectURL(answersBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    // Simulate loading delay and show results
    setTimeout(() => {
      loading.classList.add("hidden");
      results.classList.remove("hidden");
      document.getElementById("question-section").classList.add("hidden");
      document.getElementById("navigation").classList.add("hidden");
    }, 2000); // 2-second loading delay
  });
});
