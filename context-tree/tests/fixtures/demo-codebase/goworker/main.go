package main

import (
	"fmt"

	"example.com/taskflow/goworker/worker"
)

func main() {
	cfg := worker.DefaultConfig()
	pool := worker.NewPool(cfg)
	fmt.Println(pool.Run("default"))
}
