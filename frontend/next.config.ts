import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Set output file tracing root to workspace root
  outputFileTracingRoot: path.join(__dirname, ".."),
  
  // Enable transpiling packages from workspace
  transpilePackages: ['shared'],
  
  // Ensure environment variables are available
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL,
  },
  
  // Enable Turbopack (Next.js 16+)
  turbopack: {
    resolveAlias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  // Webpack config for fallback (if --webpack flag is used)
  webpack: (config, { isServer }) => {
    // Explicitly configure @ alias to ensure it works in all environments
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './src'),
    };
    
    // Preserve existing resolve.modules and add workspace root node_modules
    const existingModules = config.resolve.modules || ['node_modules'];
    config.resolve.modules = [
      ...existingModules,
      path.resolve(__dirname, "../node_modules"),
    ];
    
    // Preserve existing resolveLoader.modules and add workspace root
    const existingLoaderModules = config.resolveLoader?.modules || ['node_modules'];
    if (!config.resolveLoader) {
      config.resolveLoader = {};
    }
    config.resolveLoader.modules = [
      ...existingLoaderModules,
      path.resolve(__dirname, "../node_modules"),
    ];
    
    return config;
  },
};

export default nextConfig;
