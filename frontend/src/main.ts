interface CommandResponse {
  received_prompt: string;
  reply: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const input = document.getElementById("promptInput") as HTMLInputElement;
const button = document.getElementById("sendBtn") as HTMLButtonElement;
const responseArea = document.getElementById("responseArea") as HTMLParagraphElement;

button.addEventListener("click", async () => {
  const promptText = input.value.trim();
  if (!promptText) return;

  const response = await fetch(`${API_BASE_URL}/api/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptText }),
  });

  const data: CommandResponse = await response.json();
  responseArea.textContent = data.reply;
});