import type { NextConfig } from "next";

const EDGE_URL = "https://edgefhir-relay-1.onrender.com";

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
