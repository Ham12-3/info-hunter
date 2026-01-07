"use client";

import { motion, useReducedMotion } from "framer-motion";
import React, { memo } from "react";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  variant?: "primary" | "secondary";
};

const GlassButton = memo(function GlassButton({ loading, variant = "primary", className = "", children, ...props }: Props) {
  const reduce = useReducedMotion();

  const baseClasses = "relative overflow-hidden rounded-2xl px-5 py-3 font-medium focus:outline-none focus:ring-2 focus:ring-sky-400/60 disabled:opacity-60 disabled:cursor-not-allowed transition-all";
  
  const variantClasses = variant === "primary" 
    ? "glass glass-noise text-slate-900 bg-primary-500/20 hover:bg-primary-500/30"
    : "glass glass-noise text-slate-700 bg-white/20 hover:bg-white/30";

  return (
    <motion.button
      whileHover={reduce ? undefined : { scale: 1.01 }}
      whileTap={reduce ? undefined : { scale: 0.98 }}
      transition={{ type: "spring", stiffness: 380, damping: 26 }}
      className={`${baseClasses} ${variantClasses} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {/* moving highlight */}
      {!reduce && (
        <span
          className="pointer-events-none absolute -inset-10 opacity-30"
          style={{
            background:
              "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.65) 50%, transparent 100%)",
            transform: "translateX(-120%) rotate(12deg)",
            animation: "glass-shine 4.8s ease-in-out infinite",
          }}
        />
      )}

      <span className="relative z-10 flex items-center justify-center gap-2">
        {loading ? "Loading…" : children}
      </span>
    </motion.button>
  );
});

export default GlassButton;

