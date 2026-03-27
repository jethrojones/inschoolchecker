import type { NextConfig } from "next";

const isGithubPages = process.env.GITHUB_ACTIONS === "true";
const rawBasePath = process.env.PAGES_BASE_PATH?.trim();
const pagesBasePath = rawBasePath
  ? rawBasePath.startsWith("/")
    ? rawBasePath.replace(/\/+$/, "")
    : `/${rawBasePath.replace(/\/+$/, "")}`
  : "";

const nextConfig: NextConfig = {
  experimental: {
    typedRoutes: false,
  },
  transpilePackages: ["@inschoolchecker/shared-types"],
  output: "export",
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  ...(isGithubPages && pagesBasePath
    ? {
        basePath: pagesBasePath,
        assetPrefix: `${pagesBasePath}/`,
      }
    : {}),
};

export default nextConfig;
