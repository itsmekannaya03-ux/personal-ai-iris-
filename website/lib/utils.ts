import { clsx, type ClassValue } from "clsx"

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatPrice(price: number, currency = "INR"): string {
  if (currency === "INR") {
    return `₹${price.toLocaleString("en-IN")}`
  }
  return `$${price.toLocaleString("en-US")}`
}
