/**
 * Utility Functions
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with clsx
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format percentage
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format time from seconds
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Check if date is expired
 */
export function isExpired(expiresAt: string): boolean {
  const now = new Date();
  const expires = new Date(expiresAt);
  return now > expires;
}

/**
 * Parse percentage string to number
 */
export function parsePercent(prob: string): number {
  return parseFloat(prob.replace("%", "")) / 100;
}
