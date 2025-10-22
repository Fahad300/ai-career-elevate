/**
 * Merge class names conditionally, ignoring falsy values.
 */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}