package worker

// Config controls pool sizing and retry behavior.
type Config struct {
	Concurrency int
	MaxAttempts int
}

// DefaultConfig mirrors pyserver's dispatcher defaults.
func DefaultConfig() Config {
	return Config{Concurrency: 4, MaxAttempts: 3}
}
