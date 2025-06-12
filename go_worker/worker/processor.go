package worker

import (
	"fmt"
	"io"
	"net/http"
)

// Add100 接收整数，返回整数加 100
func Add100(task interface{}) (interface{}, error) {
	n, ok := task.(int)
	if !ok {
		return nil, fmt.Errorf("invalid type for Add100")
	}
	return n + 100, nil
}

// Fibonacci 递归计算第 n 个斐波那契数
func Fibonacci(task interface{}) (interface{}, error) {
	n, ok := task.(int)
	if !ok {
		return nil, fmt.Errorf("invalid task type: expected int")
	}
	if n <= 0 {
		return nil, fmt.Errorf("n must be a positive integer")
	}
	if n == 1 || n == 2 {
		return 1, nil
	}
	// 递归调用
	a, err := Fibonacci(n - 1)
	if err != nil {
		return nil, err
	}
	b, err := Fibonacci(n - 2)
	if err != nil {
		return nil, err
	}
	return a.(int) + b.(int), nil
}

// HTTPProcessor 接收字符串 URL，返回响应长度
func HTTPProcessor(task interface{}) (interface{}, error) {
	url, ok := task.(string)
	if !ok {
		return nil, fmt.Errorf("invalid task type: expected string URL")
	}

	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("HTTP GET error: %v", err)
	}
	defer resp.Body.Close()

	// 也可以读取内容长度
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read body error: %v", err)
	}

	return fmt.Sprintf("Status: %d, Length: %d", resp.StatusCode, len(body)), nil
}
