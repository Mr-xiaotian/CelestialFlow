package worker

// 标准任务结构
type TaskPayload struct {
	ID     string `json:"id"`
	Task   any    `json:"task"`
	EmitTs int64  `json:"emit_ts"` // 任务创建时间
}

// 函数签名定义
type TaskParser func(any) ([]any, error)
type TaskProcessor func([]any) (any, error)
