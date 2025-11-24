import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Set output file tracing root to workspace root
  outputFileTracingRoot: path.join(__dirname, ".."),
  
  // Enable transpiling packages from workspace
  transpilePackages: ['shared'],
  
  // Configure webpack to resolve modules from workspace root
  webpack: (config, { isServer }) => {
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
