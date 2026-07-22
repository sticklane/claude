// Fixture: original implementation of a discount calculator.
// Deliberately duplicated verbatim into discount-clone.ts so the
// clone-audit recipe has a known TS clone to rediscover.
export function calculateOrderDiscount(
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
