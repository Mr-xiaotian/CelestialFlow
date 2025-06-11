package worker

import "encoding/json"

// 标准任务结构
type TaskPayload struct {
	ID   string          `json:"id"`
	Task json.RawMessage `json:"task"`
}

// 函数签名定义
type TaskParser func(json.RawMessage) (interface{}, error)
type TaskProcessor func(interface{}) (interface{}, error)
