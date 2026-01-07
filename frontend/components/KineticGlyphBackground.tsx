"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

type Props = {
  className?: string;
  glyphs?: string; // characters used in the grid
  density?: number; // px per cell, lower = denser
};

export default function KineticGlyphBackground({
  className = "",
  glyphs = "·•:*+×⌁⌂⌃⌄⌥⌘⌇",
  density = 48, // Increased from 34 to reduce DOM nodes
}: Props) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const mouse = useRef({ x: -9999, y: -9999 });
  const raf = useRef<number | null>(null);

  // Resize observer for correct grid size
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    const ro = new ResizeObserver((entries) => {
      const r = entries[0]?.contentRect;
      if (!r) return;
      setSize({ w: Math.floor(r.width), h: Math.floor(r.height) });
    });

    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Pointer tracking (local coords)
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    const onMove = (e: PointerEvent) => {
      const rect = el.getBoundingClientRect();
      mouse.current.x = e.clientX - rect.left;
      mouse.current.y = e.clientY - rect.top;
    };

    const onLeave = () => {
      mouse.current.x = -9999;
      mouse.current.y = -9999;
    };

    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);

    return () => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  const cols = Math.max(1, Math.floor(size.w / density));
  const rows = Math.max(1, Math.floor(size.h / density));

  // Stable random glyph per cell
  const cells = useMemo(() => {
    const total = cols * rows;
    const arr = new Array(total).fill(0).map((_, i) => {
      const ch = glyphs[Math.floor((Math.sin(i * 999) + 1) * 0.5 * (glyphs.length - 1))] ?? "·";
      const seed = (Math.sin(i * 123.456) + 1) * 0.5; // 0..1
      return { ch, seed };
    });
    return arr;
  }, [cols, rows, glyphs]);

  // Animate with CSS variables for cursor - throttled for performance
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    let lastUpdate = 0;
    const throttleMs = 16; // ~60fps instead of unlimited

    const tick = (timestamp: number) => {
      if (timestamp - lastUpdate >= throttleMs) {
        el.style.setProperty("--mx", `${mouse.current.x}px`);
        el.style.setProperty("--my", `${mouse.current.y}px`);
        lastUpdate = timestamp;
      }
      raf.current = requestAnimationFrame(tick);
    };

    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, []);

  return (
    <div ref={wrapRef} className={`absolute inset-0 overflow-hidden ${className}`}>
      {/* soft gradient wash - tuned for light blue background */}
      <div className="absolute inset-0 opacity-60 [background:radial-gradient(80%_60%_at_20%_10%,rgba(56,189,248,0.25),transparent_60%),radial-gradient(70%_50%_at_90%_20%,rgba(167,139,250,0.22),transparent_55%),radial-gradient(70%_60%_at_60%_90%,rgba(125,211,252,0.18),transparent_55%)]" />

      {/* glyph grid */}
      <div
        className="absolute inset-0 grid select-none"
        style={{
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
          gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
        }}
      >
        {cells.map((c, i) => (
          <span
            key={i}
            className="glyph-cell pointer-events-none flex items-center justify-center text-[12px] sm:text-[13px] font-medium text-slate-600/30"
            style={{
              // different drift speeds
              ["--seed" as any]: c.seed,
            }}
          >
            {c.ch}
          </span>
        ))}
      </div>

      {/* Removed backdrop-blur for performance - using gradient instead */}
    </div>
  );
}

