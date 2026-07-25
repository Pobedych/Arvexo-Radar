/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep CI and Windows developer builds deterministic on constrained hosts.
  experimental: { cpus: 1 },
};

export default nextConfig;
