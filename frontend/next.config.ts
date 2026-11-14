import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Oculta el icono flotante de Next.js que solo aparece en desarrollo
  devIndicators: false,
  // Imagen Docker mínima: Next empaqueta solo lo necesario para ejecutarse (.next/standalone)
  output: "standalone",
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
