package worker

import "encoding/json"

// 示例：把 JSON 解为整数
func ParseNumberTask(raw json.RawMessage) (interface{}, error) {
	var n int
	err := json.Unmarshal(raw, &n)
	return n, err
}
