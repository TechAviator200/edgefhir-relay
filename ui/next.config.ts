import type { NextConfig } from "next";

const EDGE_URL =
  process.env.NEXT_PUBLIC_EDGE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${EDGE_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
