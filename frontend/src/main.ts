interface CommandResponse {
  received_prompt: string;
  reply: string;
  conversation_id: string | null;
  needs_clarification: boolean;
  missing_fields: Array<"product" | "quantity" | "client">;
  order_ready: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const input = document.getElementById("promptInput") as HTMLInputElement;
const button = document.getElementById("sendBtn") as HTMLButtonElement;
const responseArea = document.getElementById("responseArea") as HTMLParagraphElement;

// Keeps the backend conversation context so clarification answers (e.g. "5") are understood.
let conversationId: string | null = null;

button.addEventListener("click", async () => {
  const promptText = input.value.trim();
  if (!promptText) return;

  const response = await fetch(`${API_BASE_URL}/api/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptText, conversation_id: conversationId }),
  });

  const data: CommandResponse = await response.json();
  conversationId = data.conversation_id;
  responseArea.textContent = data.reply;
  if (data.needs_clarification) {
    input.value = "";
    input.focus();
  }
});
