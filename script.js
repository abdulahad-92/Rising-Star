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
  let timeLeft = 7200; // 60 + 60 minutes in seconds
  let currentQuestion = 0;
  let answers = {};

  // Uploadcare keys (replace with your keys)
  const UPLOADCARE_PUBLIC_KEY = "dd28549bfd24dc105b1e";
  const UPLOADCARE_SECRET_KEY = "4f3c2b1a0f373234b53b";

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

  // Submit test with Uploadcare REST API and FormSubmit
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
          correctness: answers[i].correctness || "pending",
        });
      } else {
        answersArray.push({
          id: questions[i].id,
          selected_option: "skipped",
          correctness: "not attempted",
        });
      }
    }

    // Generate JSON file with student details
    const timestamp = new Date()
      .toISOString()
      .replace(/[-:]/g, "")
      .slice(0, 15);
    const filename = `student_answers_${timestamp}.json`;
    const answersData = {
      student_id: studentInfo.phone || Date.now(),
      name: studentInfo.name || "N/A",
      phone: studentInfo.phone || "N/A",
      answers: answersArray,
    };
    const answersBlob = new Blob([JSON.stringify(answersData, null, 2)], {
      type: "application/json",
    });
    const answersFile = new File([answersBlob], filename);

    let cdnUrl = "";
    let uploadFailed = false;

    try {
      // Step 1: Attempt Upload to Uploadcare
      const formData = new FormData();
      formData.append("UPLOADCARE_PUB_KEY", UPLOADCARE_PUBLIC_KEY);
      formData.append("UPLOADCARE_STORE", "1");
      formData.append("file", answersFile);

      const uploadResponse = await fetch(
        "https://upload.uploadcare.com/base/",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!uploadResponse.ok) {
        throw new Error(
          `Uploadcare upload failed: ${uploadResponse.statusText}`
        );
      }

      const uploadResult = await uploadResponse.json();
      const fileId = uploadResult.file;
      cdnUrl = `https://ucarecdn.com/${fileId}/`;
      console.log("Uploadcare upload successful:", cdnUrl);
    } catch (error) {
      console.error("Uploadcare upload failed:", error);
      uploadFailed = true;
    }

    // Step 2: Prepare FormSubmit data
    answersUrlInput.value = cdnUrl;

    // Add filename to form data
    const hiddenFilenameInput = document.createElement("input");
    hiddenFilenameInput.type = "hidden";
    hiddenFilenameInput.name = "json_filename";
    hiddenFilenameInput.value = filename;
    registrationForm.appendChild(hiddenFilenameInput);

    // If Uploadcare failed, include raw JSON in FormSubmit
    if (uploadFailed) {
      const hiddenJsonInput = document.createElement("input");
      hiddenJsonInput.type = "hidden";
      hiddenJsonInput.name = "raw_json";
      hiddenJsonInput.value = JSON.stringify(answersData, null, 2);
      registrationForm.appendChild(hiddenJsonInput);
      console.log("Added raw JSON to FormSubmit as backup");
    }

    // Step 3: Submit to FormSubmit
    try {
      registrationForm.action =
        "https://formsubmit.co/abdulahadchachar92@gmail.com";
      registrationForm.method = "POST";

      const formResponse = await fetch(registrationForm.action, {
        method: "POST",
        body: new FormData(registrationForm),
        headers: { Accept: "application/json" },
      });

      if (formResponse.ok) {
        console.log("FormSubmit email sent successfully");
        results.classList.remove("hidden");
        document.getElementById(
          "result-text"
        ).textContent = `Thank you, ${studentInfo.name}! Your report will be shared soon via WhatsApp.`;
        document.getElementById("question-section").classList.add("hidden");
        document.getElementById("navigation").classList.add("hidden");
      } else {
        throw new Error(
          `FormSubmit submission failed: ${formResponse.statusText}`
        );
      }
    } catch (error) {
      console.error("FormSubmit submission error:", error);
      alert(
        "An error occurred during submission. Please email your answers to abdulahadchachar92@gmail.com."
      );
    } finally {
      loading.classList.add("hidden");
    }
  });
});
