.PHONY: run-worker build-worker

# 运行 go_worker/main.go
run-worker:
	cd go_worker && go run main.go

# 编译 go_worker 为二进制
build-worker:
	cd go_worker && go build -o redis_worker main.go
