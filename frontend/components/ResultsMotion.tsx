"use client";

import { motion, useReducedMotion } from "framer-motion";
import React, { memo } from "react";

export const ResultsList = memo(function ResultsList({ children }: { children: React.ReactNode }) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: { staggerChildren: reduce ? 0 : 0.04, delayChildren: reduce ? 0 : 0.02 },
        },
      }}
    >
      {children}
    </motion.div>
  );
});

export const ResultCard = memo(function ResultCard({ children }: { children: React.ReactNode }) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      variants={{
        hidden: reduce ? { opacity: 0 } : { opacity: 0, y: 8 },
        show: reduce ? { opacity: 1 } : { opacity: 1, y: 0 },
      }}
      transition={{ type: "spring", stiffness: 300, damping: 25, mass: 0.6 }}
      whileHover={reduce ? undefined : { y: -1 }}
      style={{ willChange: 'transform' }}
    >
      {children}
    </motion.div>
  );
});

