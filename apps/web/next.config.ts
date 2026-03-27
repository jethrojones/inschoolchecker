import type { NextConfig } from "next";

const isGithubPages = process.env.GITHUB_ACTIONS === "true";
const repoName = "inschoolchecker";

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
  ...(isGithubPages
    ? {
        basePath: `/${repoName}`,
        assetPrefix: `/${repoName}/`,
      }
    : {}),
};

export default nextConfig;
