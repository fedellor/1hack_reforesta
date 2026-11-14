import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Oculta el icono flotante de Next.js que solo aparece en desarrollo
  devIndicators: false,
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
