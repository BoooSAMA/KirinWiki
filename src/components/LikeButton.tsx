import { useState, useEffect, useCallback } from "preact/hooks";

interface Props {
  slug: string;
}

export default function LikeButton({ slug }: Props) {
  const [count, setCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [animating, setAnimating] = useState(false);

  const fetchCount = useCallback(async () => {
    try {
      const res = await fetch(`/api/likes?slug=${encodeURIComponent(slug)}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setCount(data.count);
    } catch {
      setCount(0);
    }
  }, [slug]);

  useEffect(() => {
    fetchCount();
  }, [fetchCount]);

  const handleLike = async () => {
    if (loading) return;
    setLoading(true);

    try {
      const res = await fetch("/api/likes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug }),
      });
      if (!res.ok) throw new Error("Failed to like");
      const data = await res.json();
      setCount(data.count);
      setAnimating(true);
      setTimeout(() => setAnimating(false), 400);
    } catch {
      // Silently fail — count stays unchanged
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleLike}
      disabled={loading || count === null}
      class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl
             bg-white/60 border border-white/40
             hover:bg-white/60 hover:shadow-md hover:-translate-y-0.5
             active:translate-y-0 active:shadow-sm
             disabled:opacity-50 disabled:cursor-not-allowed
             transition-all duration-200 text-gray-600 text-sm
             cursor-pointer select-none"
      title="Like this page"
    >
      <span
        class={`text-lg transition-transform duration-300 ${
          animating ? "scale-125" : "scale-100"
        }`}
        style={{ display: "inline-block" }}
      >
        ❤️
      </span>
      <span class="font-medium tabular-nums min-w-[1.5rem] text-center">
        {count === null ? "…" : count}
      </span>
    </button>
  );
}
