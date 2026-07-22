const statusMessage = document.querySelector("#status");
const startedAt = Date.now();
const pollDelay = 3000;
const readyChecksNeeded = 3;
let readyChecks = 0;

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
    const response = await fetch(`/api/health?_=${Date.now()}`, { cache: "no-store" });
    const result = await response.json();

    if (response.status === 500) {
      statusMessage.textContent = "DayMap is not configured yet. Please try again later.";
      return;
    }

    if (result.ready && result.appUrl) {
      readyChecks += 1;

      if (readyChecks >= readyChecksNeeded) {
        statusMessage.textContent = "DayMap is ready. Opening it now.";

        const destination = new URL(result.appUrl);
        destination.searchParams.set("_daymap_start", Date.now().toString());
        window.setTimeout(() => window.location.replace(destination.toString()), 750);
        return;
      }

      statusMessage.textContent = `DayMap is responding. Finishing startup (${readyChecks}/${readyChecksNeeded}).`;
    } else {
      readyChecks = 0;
      updateWaitingMessage();
    }
  } catch {
    readyChecks = 0;
    statusMessage.textContent = "DayMap is still starting. Retrying shortly.";
  }

  window.setTimeout(checkHealth, pollDelay);
}

checkHealth();
