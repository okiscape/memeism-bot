/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['@kisa/shared'],
};

module.exports = nextConfig;
