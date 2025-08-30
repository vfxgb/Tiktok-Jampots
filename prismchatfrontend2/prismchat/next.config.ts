import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "izwlelghcodjuiyakevi.supabase.co",
        pathname: "/storage/v1/object/public/**",
      },
    ],
    unoptimized: true,
  },
};

export default nextConfig;
