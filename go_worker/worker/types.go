package worker

// 标准任务结构
type TaskPayload struct {
	ID   string      `json:"id"`
	Task interface{} `json:"task"`
}

// 函数签名定义
type TaskParser func(interface{}) ([]interface{}, error)
type TaskProcessor func([]interface{}) (interface{}, error)
