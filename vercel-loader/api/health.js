const healthPath = "/_stcore/health";
const timeoutMs = 8000;

function sendJson(response, status, body) {
  response.setHeader("Cache-Control", "no-store, max-age=0");
  return response.status(status).json(body);
}

function getAppUrl(value) {
  try {
    const url = new URL(value);

    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
      return null;
    }

    return url.origin;
  } catch {
    return null;
  }
}

module.exports = async function health(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return sendJson(response, 405, { ready: false });
  }

  const appUrl = getAppUrl(process.env.DAYMAP_APP_URL);

  if (!appUrl) {
    return sendJson(response, 500, {
      ready: false,
      error: "DAYMAP_APP_URL is not configured.",
    });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const renderResponse = await fetch(`${appUrl}${healthPath}`, {
      cache: "no-store",
      headers: { Accept: "text/plain" },
      signal: controller.signal,
    });

    if (!renderResponse.ok) {
      return sendJson(response, 503, { ready: false });
    }

    return sendJson(response, 200, { ready: true, appUrl });
  } catch {
    return sendJson(response, 503, { ready: false });
  } finally {
    clearTimeout(timeout);
  }
};
