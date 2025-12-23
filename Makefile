# 目标可执行文件路径
GO_WORKER_EXE = go_worker/go_worker.exe

# 需要监视更新的源文件
GO_WORKER_SOURCES = $(wildcard go_worker/*.go) $(wildcard go_worker/worker/*.go)

# 默认目标
.PHONY: all
all: run_go_worker

# 运行目标
.PHONY: run_go_worker
run_go_worker: $(GO_WORKER_EXE)
	@$(GO_WORKER_EXE)

# 构建目标
$(GO_WORKER_EXE): $(GO_WORKER_SOURCES)
	cd go_worker && go build -o go_worker.exe

# 清理目标
.PHONY: clean
clean:
	rm -f $(GO_WORKER_EXE)