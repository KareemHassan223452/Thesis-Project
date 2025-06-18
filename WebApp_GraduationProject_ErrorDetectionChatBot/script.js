// Function to scroll to bottom smoothly
function scrollToBottom() {
  const chatMessages = document.getElementById('chat-messages');
  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: 'smooth'
  });
}

// Function to format code for display
function formatCode(code) {
  return code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function analyzeCode() {
  const codeInput = document.getElementById('user-input');
  const chatMessages = document.getElementById('chat-messages');
  const sendButton = document.getElementById('send-btn');
  const code = codeInput.value;

  if (!code.trim()) {
    return;
  }

  // Disable button and show loading state
  sendButton.disabled = true;
  sendButton.textContent = 'Analyzing...';

  // Add user's code to chat
  const userMessage = document.createElement('div');
  userMessage.className = 'message user-message';
  userMessage.innerHTML = `<pre>${formatCode(code)}</pre>`;
  chatMessages.appendChild(userMessage);
  scrollToBottom();

  try {
    console.log('Sending request to server...');
    const response = await fetch('http://localhost:8000/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ code: code })
    });

    console.log('Response status:', response.status);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Received data:', data);
    
    // Add bot's response to chat
    const botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';
    botMessage.innerHTML = `
      <div class="cwe-info">
        <h3>CWE-${data.cwe_id}: ${data.cwe_name}</h3>
        <p><strong>Label:</strong> ${data.label_name}</p>
        <p>${data.description}</p>
      </div>
    `;
    chatMessages.appendChild(botMessage);
    scrollToBottom();

    // Clear input
    codeInput.value = '';
    
  } catch (error) {
    console.error('Error:', error);
    const errorMessage = document.createElement('div');
    errorMessage.className = 'message bot-message error';
    errorMessage.innerHTML = `Error: ${error.message}`;
    chatMessages.appendChild(errorMessage);
    scrollToBottom();
  } finally {
    // Re-enable button and restore text
    sendButton.disabled = false;
    sendButton.textContent = 'Analyze Code';
  }
}

// Initialize event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Handle Enter key in textarea
  document.getElementById('user-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      analyzeCode();
    }
  });

  // Auto-resize textarea
  document.getElementById('user-input').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
  });
});