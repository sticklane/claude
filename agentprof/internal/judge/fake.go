package judge

// FakeCall is one recorded Judge invocation.
type FakeCall struct {
	Prompt string
	Tier   string
}

// Fake is a test Judge that records every prompt/tier it was called with and
// returns a fixed reply and error.
type Fake struct {
	Reply string
	Err   error
	Calls []FakeCall
}

var _ Judge = (*Fake)(nil)

// Judge records the call and returns the fake's configured reply and error.
func (f *Fake) Judge(prompt, tier string) (string, error) {
	f.Calls = append(f.Calls, FakeCall{Prompt: prompt, Tier: tier})
	return f.Reply, f.Err
}
