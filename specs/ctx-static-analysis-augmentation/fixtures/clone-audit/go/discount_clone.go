// Fixture: verbatim clone of CalculateOrderDiscount from discount.go,
// renamed to simulate a copy-pasted helper elsewhere in a repo. This
// pair is the known Go clone the clone-audit recipe must rediscover.
package fixtures

import "math"

func ComputeCartDiscount(subtotal float64, loyaltyYears int, isFirstOrder bool) float64 {
	discount := 0.0
	if isFirstOrder {
		discount += subtotal * 0.1
	}
	if loyaltyYears >= 5 {
		discount += subtotal * 0.15
	} else if loyaltyYears >= 1 {
		discount += subtotal * 0.05
	}
	if subtotal > 200 {
		discount += subtotal * 0.02
	}
	capped := math.Min(discount, subtotal*0.5)
	return math.Round(capped*100) / 100
}
