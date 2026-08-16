import path from "node:path";
import { config as loadEnv } from "dotenv";
import type { NextConfig } from "next";

loadEnv({ path: path.resolve(process.cwd(), "../../.env"), quiet: true });

const nextConfig: NextConfig = {
  poweredByHeader: false,
};

export default nextConfig;
