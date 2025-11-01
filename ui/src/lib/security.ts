/**
 * Escapes HTML special characters to prevent XSS attacks
 */
export function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Validates that a string contains only emoji characters and whitespace
 * This provides an additional layer of security for emoji fields
 */
export function isValidEmoji(str: string): boolean {
  // Basic check: emojis should be short (1-10 chars) and not contain HTML special chars
  if (str.length === 0 || str.length > 10) return false;
  if (/<|>|&|"|'/.test(str)) return false;
  return true;
}

/**
 * Sanitizes emoji input by escaping HTML and validating format
 */
export function sanitizeEmoji(emoji: string): string {
  if (!isValidEmoji(emoji)) {
    console.warn("Invalid emoji detected, using fallback");
    return "📍"; // Fallback emoji
  }
  return escapeHtml(emoji);
}
