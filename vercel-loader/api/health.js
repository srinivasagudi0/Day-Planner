const healthPath = "/_stcore/health";
const timeoutMs = 8000;

function sendJson(response, status, body) {
  response.setHeader("Cache-Control", "no-store, max-age=0");
  response.setHeader("CDN-Cache-Control", "no-store");
  response.setHeader("Vercel-CDN-Cache-Control", "no-store");
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
    const cacheBuster = Date.now().toString();
    const rootUrl = new URL(appUrl);
    const healthUrl = new URL(healthPath, appUrl);
    rootUrl.searchParams.set("_daymap_wake", cacheBuster);
    healthUrl.searchParams.set("_daymap_wake", cacheBuster);

    const [rootResponse, healthResponse] = await Promise.all([
      fetch(rootUrl, {
        cache: "no-store",
        headers: { Accept: "text/html" },
        signal: controller.signal,
      }),
      fetch(healthUrl, {
        cache: "no-store",
        headers: { Accept: "text/plain" },
        signal: controller.signal,
      }),
    ]);

    if (!rootResponse.ok || !healthResponse.ok) {
      return sendJson(response, 503, { ready: false });
    }

    const contentType = rootResponse.headers.get("content-type") || "";
    const page = await rootResponse.text();

    if (!contentType.includes("text/html") || !page.trim()) {
      return sendJson(response, 503, { ready: false });
    }

    return sendJson(response, 200, { ready: true, appUrl });
  } catch {
    return sendJson(response, 503, { ready: false });
  } finally {
    clearTimeout(timeout);
  }
};
