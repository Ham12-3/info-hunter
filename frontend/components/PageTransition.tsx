"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import React from "react";

export default function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const reduce = useReducedMotion();

  const variants = {
    initial: reduce ? { opacity: 0 } : { opacity: 0, y: 8, filter: "blur(6px)" },
    animate: reduce ? { opacity: 1 } : { opacity: 1, y: 0, filter: "blur(0px)" },
    exit: reduce ? { opacity: 0 } : { opacity: 0, y: -6, filter: "blur(6px)" },
  };

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        variants={variants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.22, ease: "easeOut" }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

