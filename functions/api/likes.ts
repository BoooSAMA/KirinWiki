interface Env {
  DB: D1Database;
}

interface LikeRow {
  slug: string;
  count: number;
}

function corsHeaders(): HeadersInit {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const url = new URL(request.url);

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  if (request.method === "GET") {
    const slug = url.searchParams.get("slug");
    if (!slug) {
      return json({ error: "Missing slug parameter" }, 400);
    }

    const stmt = env.DB.prepare("SELECT slug, count FROM likes WHERE slug = ?").bind(slug);
    const result = await stmt.first<LikeRow>();

    return json({ slug, count: result?.count ?? 0 });
  }

  if (request.method === "POST") {
    let body: { slug?: string };
    try {
      body = await request.json();
    } catch {
      return json({ error: "Invalid JSON body" }, 400);
    }

    if (!body.slug) {
      return json({ error: "Missing slug in request body" }, 400);
    }

    const slug = body.slug;

    const stmt = env.DB.prepare(
      "INSERT INTO likes (slug, count) VALUES (?, 1) ON CONFLICT(slug) DO UPDATE SET count = count + 1 RETURNING slug, count"
    ).bind(slug);

    const result = await stmt.first<LikeRow>();

    return json({ slug: result!.slug, count: result!.count });
  }

  return json({ error: "Method not allowed" }, 405);
};
