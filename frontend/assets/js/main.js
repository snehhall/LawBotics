// File Upload Handling
const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const docPreview = document.getElementById("docPreview");
const processingIndicator = document.getElementById("processingIndicator");

// Chatbot Handling
const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Handle file selection
dropArea.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", handleFiles);

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(eventName, highlight, false);
});

["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, unhighlight, false);
});

const formData = new FormData();
formData.append("file", fileInput.files[0]);
fetch("http://localhost:5000/api/upload", {
  method: "POST",
  body: formData,
})
  .then((res) => res.json())
  .then((data) => console.log(data));

function highlight() {
  dropArea.classList.add("bg-indigo-100");
}

function unhighlight() {
  dropArea.classList.remove("bg-indigo-100");
}

function handleFiles(e) {
  const files = e.target.files || e.dataTransfer.files;
  if (files.length) {
    fileInput.files = files;
    updateFileInfo(files[0]);
  }
}

// Update your fetch calls to use the correct endpoint
async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://localhost:5000/api/upload", {
      method: "POST",
      body: formData,
    });
    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    throw new Error("Failed to upload file. Please try again.");
  }
}

function updateFileInfo(file) {
  document.getElementById("docName").textContent = file.name;
  analyzeBtn.disabled = false;
}

// Analyze Document
analyzeBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  processingIndicator.classList.remove("hidden");
  analyzeBtn.disabled = true;

  try {
    const data = await uploadFile(file);

    if (data.error) {
      throw new Error(data.error);
    }

    displayAnalysisResults(data);
  } catch (error) {
    docPreview.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
  } finally {
    processingIndicator.classList.add("hidden");
    analyzeBtn.disabled = false;
  }
});

function displayAnalysisResults(data) {
  docPreview.innerHTML = `
        <div class="space-y-6">
            <div>
                <h4 class="font-semibold text-lg mb-2">Document Summary</h4>
                <p class="text-gray-700">${data.summary}</p>
            </div>
            <div>
                <h4 class="font-semibold text-lg mb-2">Simplified Text</h4>
                <div class="bg-gray-100 p-4 rounded">${
                  data.simplified_text
                }</div>
            </div>
            <div>
                <h4 class="font-semibold text-lg mb-2">Key Analysis</h4>
                <ul class="list-disc pl-5 space-y-1">
                    ${data.analysis.key_clauses
                      .map((clause) => `<li>${clause}</li>`)
                      .join("")}
                </ul>
            </div>
        </div>
    `;
}

// Chatbot Functionality
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Add user message to chat
  addMessage(message, "user");
  userInput.value = "";

  try {
    // Get document context (simplified)
    const docContext = docPreview.textContent || "general legal principles";

    const response = await fetch("http://localhost:5000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: message,
        context: docContext,
      }),
    });

    const data = await response.json();
    addMessage(data.response, "bot");

    // Add sources if available
    if (data.sources && data.sources.length) {
      addMessage(
        `Sources: ${data.sources.join(", ")}`,
        "bot",
        "text-sm text-gray-500"
      );
    }
  } catch (error) {
    addMessage("Sorry, I encountered an error processing your request.", "bot");
  }
}

function addMessage(text, sender, additionalClasses = "") {
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${sender} p-3 mb-2 ${additionalClasses}`;
  messageDiv.innerHTML = `<p>${text}</p>`;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Sample document buttons
document.querySelectorAll(".sample-doc-btn").forEach((btn) => {
  btn.addEventListener("click", async function () {
    const filename = this.dataset.file;
    const response = await fetch(`/sample-docs/${filename}`);

    if (!response.ok) {
      addMessage("Error loading sample document.", "bot");
      return;
    }

    const content = await response.text();

    // Simulate file upload
    const file = new File([content], filename, { type: "text/plain" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    updateFileInfo(file);
  });
});
