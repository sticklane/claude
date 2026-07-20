package worker

import "fmt"

// Pool consumes tasks from a named queue.
type Pool struct {
	cfg Config
}

func NewPool(cfg Config) *Pool {
	return &Pool{cfg: cfg}
}

func (p *Pool) Run(queue string) string {
	return fmt.Sprintf("pool(%d) draining %s", p.cfg.Concurrency, queue)
}
