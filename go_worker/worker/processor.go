package worker

import "fmt"

// 示例处理函数
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
