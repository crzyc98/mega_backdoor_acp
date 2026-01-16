/**
 * Rate conversion utilities for frontend-backend communication.
 *
 * The backend API expects decimal rates (0.0 to 1.0), but users think
 * in percentages (0 to 100). These utilities handle the conversion.
 *
 * Examples:
 * - User enters "6" (meaning 6%) -> API receives 0.06
 * - User enters "75" (meaning 75%) -> API receives 0.75
 */

/**
 * Convert a percentage value (0-100) to a decimal (0.0-1.0).
 *
 * @param percent - The percentage value (e.g., 6 for 6%, 75 for 75%)
 * @returns The decimal value (e.g., 0.06, 0.75)
 */
export function percentToDecimal(percent: number): number {
  return percent / 100;
}

/**
 * Convert a decimal value (0.0-1.0) to a percentage (0-100).
 *
 * @param decimal - The decimal value (e.g., 0.06, 0.75)
 * @returns The percentage value (e.g., 6, 75)
 */
export function decimalToPercent(decimal: number): number {
  return decimal * 100;
}

/**
 * Validate that a rate value is within the valid decimal range (0.0 to 1.0).
 *
 * @param value - The rate value to validate
 * @returns True if valid, false otherwise
 */
export function isValidDecimalRate(value: number): boolean {
  return value >= 0.0 && value <= 1.0;
}

/**
 * Validate that a rate value is within the valid percentage range (0 to 100).
 *
 * @param value - The rate value to validate
 * @returns True if valid, false otherwise
 */
export function isValidPercentRate(value: number): boolean {
  return value >= 0 && value <= 100;
}
