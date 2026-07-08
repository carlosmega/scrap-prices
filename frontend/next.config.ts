import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // F036: distDir aislado para builds de verificación. Dev y start usan `.next`
  // por defecto; solo el build de CI/review lo cambia vía NEXT_DIST_DIR=.next-ci
  // para no corromper el `.next/` del `next dev` del humano.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
