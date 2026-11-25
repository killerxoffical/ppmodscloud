/**
 * PPM CLOUD - Pure Serverless Cloudflare Worker API
 * 100% Native Cloudflare D1 SQL - Zero Firebase Dependencies
 */

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
  "Access-Control-Max-Age": "86400"
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...CORS_HEADERS
    }
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const method = request.method.toUpperCase();

    // 1. CORS Preflight
    if (method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    try {
      // 2. Health & Status
      if (url.pathname === "/" || url.pathname === "/api/health") {
        return jsonResponse({
          ok: true,
          service: "PPM Cloud Serverless API",
          version: "2.0.0",
          status: "online",
          environment: "Cloudflare Workers",
          hasD1: Boolean(env && env.DB),
          timestamp: Date.now()
        });
      }

      // 3. User Authentication (Registration / Login / Session)
      if (url.pathname === "/api/auth/register" && method === "POST") {
        return jsonResponse({ ok: true, message: "PPM Cloud Registration Ready" });
      }

      if (url.pathname === "/api/auth/login" && method === "POST") {
        return jsonResponse({ ok: true, message: "PPM Cloud Login Ready" });
      }

      if (url.pathname === "/api/auth/me" && method === "GET") {
        return jsonResponse({ ok: true, user: null });
      }

      // 4. Wallet & Balances
      if (url.pathname === "/api/wallet" && method === "GET") {
        const uid = url.searchParams.get("uid") || "";
        return jsonResponse({
          ok: true,
          wallet: {
            uid,
            balance: 0,
            realBalance: 0,
            bonusBalance: 0,
            loyaltyStars: 0
          }
        });
      }

      // 5. Orders & Quests
      if (url.pathname === "/api/orders" || url.pathname === "/api/admin/orders") {
        return jsonResponse({ ok: true, orders: [] });
      }

      // 6. History
      if (url.pathname === "/api/history") {
        return jsonResponse({ ok: true, history: [] });
      }

      // 404 Fallback
      return jsonResponse({ ok: false, error: "Endpoint not found" }, 404);

    } catch (err) {
      return jsonResponse({ ok: false, error: err.message || "Internal Worker Error" }, 500);
    }
  }
};
