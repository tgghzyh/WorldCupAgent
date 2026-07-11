import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "flagcdn.com",
        pathname: "/w80/**",
      },
    ],
  },
};

export default nextConfig;
