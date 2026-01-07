/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Performance optimizations
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Optimize images
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // Experimental features for better performance
  experimental: {
    optimizeCss: true,
  },
}

module.exports = nextConfig

