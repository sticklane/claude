// Package sample is a fixture for Go extraction tests.
package sample

import (
	"fmt"
	"os"
)

// GLOBAL is a package-level constant.
const GLOBAL = 10

// Value returns the sentinel CTX_SENTINEL_GODOC_3e8f marker.
//
// A second doc line so a later --doc render has more than one line.
func Value() int {
	return GLOBAL
}

// Widget is a sample struct type.
type Widget struct {
	Name string
}

// Render calls Value across symbols and touches the os package.
func (w Widget) Render() int {
	fmt.Println(w.Name)
	return Value() + os.Getpid()
}
