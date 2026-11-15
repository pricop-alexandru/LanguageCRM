interface CommandResponse {
  received_prompt: string;
  reply: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const input = document.getElementById("promptInput") as HTMLInputElement;
const button = document.getElementById("sendBtn") as HTMLButtonElement;
const chatLog = document.getElementById("chatLog") as HTMLDivElement;

function appendMessage(text: string, className: string): HTMLParagraphElement {
  const message = document.createElement("p");
  message.textContent = text;
  message.className = className;
  chatLog.appendChild(message);
  return message;
}

button.addEventListener("click", async () => {
  const promptText = input.value.trim();
  if (!promptText) return;

  input.value = "";
  button.disabled = true;

  appendMessage(promptText, "user-message");
  const loadingMessage = appendMessage("...", "loading-message");

  try {
    const response = await fetch(`${API_BASE_URL}/api/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptText }),
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data: CommandResponse = await response.json();
    loadingMessage.textContent = data.reply;
    loadingMessage.className = "bot-message";
  } catch (error) {
    loadingMessage.textContent = "Network error: could not reach the server. Please try again.";
    loadingMessage.className = "error-message";
  } finally {
    button.disabled = false;
  }
});
