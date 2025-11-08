// ------------------ FORM SUBMISSION ------------------
document.getElementById("stressForm").addEventListener("submit", async function(event) {
  event.preventDefault();

  const data = {
    username: document.getElementById("username").value,
    password: document.getElementById("password").value,
    gender: document.getElementById("gender").value,
    age: document.getElementById("age").value,
    description: document.getElementById("description").value,
    lifestyle: document.getElementById("lifestyle").value,
    lately: document.getElementById("lately").value,
    mood: document.getElementById("mood").value,
    reflection: document.getElementById("reflection").value,
    stressCauses: document.getElementById("stressCauses").value,
    handling: document.getElementById("handling").value,
    worries: document.getElementById("worries").value,
    extra: document.getElementById("extra").value,
    consent: document.getElementById("consent").checked
  };

  document.getElementById("result").classList.add("hidden");
  document.getElementById("loading").classList.remove("hidden");

  try {
    const response = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    document.getElementById("loading").classList.add("hidden");
    document.getElementById("result").classList.remove("hidden");

    // ✅ Display results from backend
    document.getElementById("stressLevel").textContent = "Stress Level: " + result.stressLevel;
    document.getElementById("confidence").textContent = "Model Confidence: " + result.confidence;
    document.getElementById("recommendations").textContent = "Generated at: " + result.timestamp;

    // ✅ Store result globally so we can download PDF later
    window.latestResult = result;

  } catch (error) {
    document.getElementById("loading").classList.add("hidden");
    console.error(error);
    alert("Error connecting to backend: " + error);
  }
});


// ------------------ PDF DOWNLOAD BUTTON ------------------
// 🔹 This goes AFTER the previous code, not inside it.
document.getElementById("downloadPdf").addEventListener("click", async function() {
  try {
    // Make sure we have a result before trying to generate PDF
    if (!window.latestResult) {
      alert("Please submit the form first to get your result!");
      return;
    }

    const response = await fetch("http://127.0.0.1:5000/generate-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(window.latestResult)
    });

    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = "stress_report.pdf";
    link.click();
  } catch (error) {
    alert("Error generating PDF: " + error);
  }
});
