package judge

// FakeCall is one recorded Judge invocation.
type FakeCall struct {
	Prompt string
	Tier   string
}

// Fake is a test Judge that records every prompt/tier it was called with and
// returns a configured reply and error.
//
// When Replies is non-empty it drives a per-call-sequenced mode: the Nth Judge
// call returns Replies[N] (0-indexed). Once Replies is exhausted, subsequent
// calls fall back to the single Reply field. An empty Replies leaves the
// original single-Reply behavior unchanged. The sequenced mode lets a test
// exercise a multi-call judge flow (e.g. the generic outcome rubric's three
// separate calls) with one shared fake instead of a locally-scripted one.
type Fake struct {
	Reply   string
	Replies []string
	Err     error
	Calls   []FakeCall
}

var _ Judge = (*Fake)(nil)

// Judge records the call and returns the fake's configured reply and error —
// the next unused Replies entry when Replies mode is active, else Reply.
func (f *Fake) Judge(prompt, tier string) (string, error) {
	reply := f.Reply
	if n := len(f.Calls); n < len(f.Replies) {
		reply = f.Replies[n]
	}
	f.Calls = append(f.Calls, FakeCall{Prompt: prompt, Tier: tier})
	return reply, f.Err
}
