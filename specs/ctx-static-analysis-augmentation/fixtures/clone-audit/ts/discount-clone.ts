// Fixture: verbatim clone of calculateOrderDiscount from discount.ts,
// renamed to simulate a copy-pasted helper elsewhere in a repo. This
// pair is the known TS clone the clone-audit recipe must rediscover.
export function computeCartDiscount(
  subtotal: number,
  loyaltyYears: number,
  isFirstOrder: boolean,
): number {
  let discount = 0;
  if (isFirstOrder) {
    discount += subtotal * 0.1;
  }
  if (loyaltyYears >= 5) {
    discount += subtotal * 0.15;
  } else if (loyaltyYears >= 1) {
    discount += subtotal * 0.05;
  }
  if (subtotal > 200) {
    discount += subtotal * 0.02;
  }
  const capped = Math.min(discount, subtotal * 0.5);
  return Math.round(capped * 100) / 100;
}
