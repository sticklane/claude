.PHONY: build test vet fixtures

build:
	go build -o agentprof .

fixtures:
	go run ./internal/fixturegen

test:
	go test ./...

vet:
	go vet ./...
