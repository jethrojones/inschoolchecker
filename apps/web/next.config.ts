import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    typedRoutes: false,
  },
  transpilePackages: ["@inschoolchecker/shared-types"],
};

export default nextConfig;
