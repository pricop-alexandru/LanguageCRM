interface CommandResponse {
  received_prompt: string;
  reply: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const input = document.getElementById("promptInput") as HTMLInputElement;
const button = document.getElementById("sendBtn") as HTMLButtonElement;
const chatLog = document.getElementById("chatLog") as HTMLDivElement;

function appendMessage(text: string, align: "user" | "bot", bubbleClass: string): HTMLDivElement {
  const row = document.createElement("div");
  row.className = `message-row ${align}`;

  const bubble = document.createElement("div");
  bubble.className = `bubble ${bubbleClass}`;
  bubble.textContent = text;

  row.appendChild(bubble);
  chatLog.appendChild(row);
  chatLog.scrollTop = chatLog.scrollHeight;
  return bubble;
}

let isSending = false;

function updateSendButtonState(): void {
  button.disabled = isSending || input.value.trim().length === 0;
}

input.addEventListener("input", updateSendButtonState);

button.addEventListener("click", async () => {
  const promptText = input.value.trim();
  if (!promptText) return;

  input.value = "";
  isSending = true;
  updateSendButtonState();

  appendMessage(promptText, "user", "bubble-user");
  const loadingMessage = appendMessage("...", "bot", "bubble-loading");

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
    loadingMessage.className = "bubble bubble-bot";
  } catch (error) {
    loadingMessage.textContent = "Network error: could not reach the server. Please try again.";
    loadingMessage.className = "bubble bubble-error";
  } finally {
    isSending = false;
    updateSendButtonState();
  }
});
