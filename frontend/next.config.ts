import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Set output file tracing root to workspace root
  outputFileTracingRoot: path.join(__dirname, ".."),
  
  // Enable transpiling packages from workspace
  transpilePackages: ['shared'],
  
  // Configure webpack to resolve modules from workspace root
  webpack: (config, { isServer }) => {
    // Add workspace root node_modules to resolve paths
    if (!config.resolve.modules) {
      config.resolve.modules = [];
    }
    config.resolve.modules.push(path.resolve(__dirname, "../node_modules"));
    config.resolve.modules.push("node_modules");
    
    // Ensure loaders can find modules in workspace root
    if (!config.resolveLoader) {
      config.resolveLoader = {};
    }
    if (!config.resolveLoader.modules) {
      config.resolveLoader.modules = [];
    }
    config.resolveLoader.modules.push(path.resolve(__dirname, "../node_modules"));
    config.resolveLoader.modules.push("node_modules");
    
    return config;
  },
};

export default nextConfig;
