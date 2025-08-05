
const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const docPreview = document.getElementById("docPreview");
const processingIndicator = document.getElementById("processingIndicator");

const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");


dropArea.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", handleFiles);
dropArea.addEventListener("drop", handleFiles);

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

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:5000/api/upload", {
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
  // Helper function to create lists safely
  function createList(items, emptyMessage = "None found") {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return `<p class="text-gray-500 italic">${emptyMessage}</p>`;
    }
    return `
      <ul class="list-disc pl-5 space-y-1">
        ${items.map(item => `<li class="text-gray-700">${item}</li>`).join("")}
      </ul>
    `;
  }

  // Helper function to format simplified text with legal terms
  function formatSimplifiedText(text) {
    if (!text) return "<p class='text-gray-500'>No simplified text available</p>";
    
    // Convert legal term explanations to proper HTML tooltips
    let formattedText = text.replace(
      /\[([^\(]+)\s*\(([^\)]+)\)\]/g,
      '<span class="legal-term relative inline-block border-b border-dashed border-indigo-500 cursor-help" title="$2">$1</span>'
    );
    
    // Add line breaks for better readability
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    return `<div class="whitespace-pre-wrap">${formattedText}</div>`;
  }

  docPreview.innerHTML = `
    <div class="space-y-8">
      <!-- Document Summary -->
      <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
        <h4 class="font-semibold text-lg mb-3 text-blue-800 flex items-center">
          <i class="fas fa-file-text mr-2"></i>Document Summary
        </h4>
        <div class="text-gray-700 leading-relaxed">
          ${data.summary || '<p class="text-gray-500 italic">No summary available</p>'}
        </div>
      </div>

      <!-- Key Analysis -->
      <div class="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg">
        <h4 class="font-semibold text-lg mb-4 text-green-800 flex items-center">
          <i class="fas fa-search mr-2"></i>Legal Analysis
        </h4>
        
        <!-- Key Clauses -->
        <div class="mb-6">
          <h5 class="font-medium text-md mb-2 text-green-700 flex items-center">
            <i class="fas fa-list-ul mr-2 text-sm"></i>Key Clauses Identified
          </h5>
          ${createList(data.analysis?.key_clauses, "No key clauses identified")}
        </div>

        <!-- Legal Obligations -->
        <div class="mb-6">
          <h5 class="font-medium text-md mb-2 text-green-700 flex items-center">
            <i class="fas fa-exclamation-triangle mr-2 text-sm"></i>Legal Obligations
          </h5>
          ${createList(data.analysis?.obligations, "No specific obligations identified")}
        </div>

        <!-- Risk Factors -->
        <div>
          <h5 class="font-medium text-md mb-2 text-green-700 flex items-center">
            <i class="fas fa-shield-alt mr-2 text-sm"></i>Risk Factors
          </h5>
          ${createList(data.analysis?.risks, "No significant risks identified")}
        </div>
      </div>

      <!-- Simplified Text -->
      <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-lg">
        <h4 class="font-semibold text-lg mb-3 text-yellow-800 flex items-center">
          <i class="fas fa-language mr-2"></i>Simplified Legal Text
          <span class="text-sm font-normal ml-2 text-yellow-600">(Hover over underlined terms for explanations)</span>
        </h4>
        <div class="bg-white p-4 rounded border max-h-96 overflow-y-auto">
          ${formatSimplifiedText(data.simplified_text)}
        </div>
      </div>

      <!-- Analysis Stats -->
      <div class="bg-gray-50 border border-gray-200 p-4 rounded-lg">
        <h4 class="font-semibold text-lg mb-3 text-gray-800 flex items-center">
          <i class="fas fa-chart-bar mr-2"></i>Analysis Statistics
        </h4>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div class="bg-white p-3 rounded shadow-sm">
            <div class="text-2xl font-bold text-indigo-600">${data.analysis?.key_clauses?.length || 0}</div>
            <div class="text-sm text-gray-600">Key Clauses</div>
          </div>
          <div class="bg-white p-3 rounded shadow-sm">
            <div class="text-2xl font-bold text-orange-600">${data.analysis?.obligations?.length || 0}</div>
            <div class="text-sm text-gray-600">Obligations</div>
          </div>
          <div class="bg-white p-3 rounded shadow-sm">
            <div class="text-2xl font-bold text-red-600">${data.analysis?.risks?.length || 0}</div>
            <div class="text-sm text-gray-600">Risk Factors</div>
          </div>
          <div class="bg-white p-3 rounded shadow-sm">
            <div class="text-2xl font-bold text-green-600">${(data.simplified_text?.match(/\[([^\(]+)\s*\(([^\)]+)\)\]/g) || []).length}</div>
            <div class="text-sm text-gray-600">Terms Simplified</div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Add tooltips for legal terms after DOM is updated
  setTimeout(() => {
    document.querySelectorAll('.legal-term').forEach(term => {
      term.addEventListener('mouseenter', function() {
        // Create tooltip if it doesn't exist
        if (!this.querySelector('.tooltip')) {
          const tooltip = document.createElement('div');
          tooltip.className = 'tooltip absolute bg-gray-800 text-white text-xs rounded py-1 px-2 z-10 -top-8 left-1/2 transform -translate-x-1/2 opacity-0 transition-opacity duration-300';
          tooltip.textContent = this.getAttribute('title');
          this.appendChild(tooltip);
          this.removeAttribute('title'); // Remove default tooltip
        }
        const tooltip = this.querySelector('.tooltip');
        if (tooltip) {
          tooltip.classList.remove('opacity-0');
          tooltip.classList.add('opacity-100');
        }
      });
      
      term.addEventListener('mouseleave', function() {
        const tooltip = this.querySelector('.tooltip');
        if (tooltip) {
          tooltip.classList.remove('opacity-100');
          tooltip.classList.add('opacity-0');
        }
      });
    });
  }, 100);
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

  // Show typing indicator
  const typingDiv = addMessage("AI is thinking...", "bot", "text-gray-500 italic");
  
  try {
    const response = await fetch("http://127.0.0.1:5000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: message,
      }),
    });

    const data = await response.json();
    
    // Remove typing indicator
    typingDiv.remove();
    
    if (data.error) {
      addMessage(`Sorry, I encountered an error: ${data.error}`, "bot", "text-red-500");
    } else {
      addMessage(data.response || "I'm not sure how to respond to that.", "bot");

      // Add sources if available
      if (data.sources && data.sources.length > 0) {
        const uniqueSources = [...new Set(data.sources)];
        addMessage(
          `📚 Sources: ${uniqueSources.join(", ")}`,
          "bot",
          "text-sm text-gray-500 mt-1"
        );
      }
    }
  } catch (error) {
    // Remove typing indicator
    typingDiv.remove();
    console.error("Chat error:", error);
    addMessage("Sorry, I'm having trouble connecting right now. Please try again.", "bot", "text-red-500");
  }
}

function addMessage(text, sender, additionalClasses = "") {
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${sender} p-3 mb-2 rounded-lg max-w-4xl ${
    sender === 'user' ? 'ml-auto' : 'mr-auto'
  } ${additionalClasses}`;
  messageDiv.innerHTML = `<p>${text}</p>`;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return messageDiv;
}

// Sample document buttons
document.querySelectorAll(".sample-doc-btn").forEach((btn) => {
  btn.addEventListener("click", async function () {
    const filename = this.dataset.file;
    
    try {
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
      
      // Auto-analyze the sample document
      setTimeout(() => {
        analyzeBtn.click();
      }, 500);
      
    } catch (error) {
      console.error("Error loading sample document:", error);
      addMessage("Sorry, couldn't load the sample document.", "bot");
    }
  });
});