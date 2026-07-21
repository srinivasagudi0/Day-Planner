const statusMessage = document.querySelector("#status");
const startedAt = Date.now();
const pollDelay = 3000;

function updateWaitingMessage() {
  const secondsWaiting = Math.round((Date.now() - startedAt) / 1000);

  if (secondsWaiting > 45) {
    statusMessage.textContent = "DayMap is still waking up. Thanks for waiting.";
  } else {
    statusMessage.textContent = "DayMap is waking up. This can take about a minute.";
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const result = await response.json();

    if (response.status === 500) {
      statusMessage.textContent = "DayMap is not configured yet. Please try again later.";
      return;
    }

    if (result.ready && result.appUrl) {
      statusMessage.textContent = "DayMap is ready. Opening it now.";
      window.location.replace(result.appUrl);
      return;
    }

    updateWaitingMessage();
  } catch {
    statusMessage.textContent = "DayMap is still starting. Retrying shortly.";
  }

  window.setTimeout(checkHealth, pollDelay);
}

checkHealth();
