// Export all shared types and utilities
export * from './types';

// Utility functions
export const formatDateTime = (date: Date): string => {
  return date.toISOString();
};

export const calculateHitRate = (hits: number, total: number): number => {
  return total > 0 ? (hits / total) * 100 : 0;
};
