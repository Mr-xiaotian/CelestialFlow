package worker

import (
	"fmt"
)

// Add100 接收一个整数参数，返回该整数加 100
func Add100(args []interface{}) (interface{}, error) {
	if len(args) != 1 {
		return nil, fmt.Errorf("Add100 expects 1 argument, got %d", len(args))
	}

	num, ok := args[0].(float64) // JSON 解析为 float64
	if !ok {
		return nil, fmt.Errorf("Add100: argument is not a number")
	}

	return int(num) + 100, nil
}

// Fibonacci 计算第 n 个斐波那契数（递归版）
func Fibonacci(args []interface{}) (interface{}, error) {
	if len(args) != 1 {
		return nil, fmt.Errorf("Fibonacci expects 1 argument, got %d", len(args))
	}

	num, ok := args[0].(float64)
	if !ok {
		return nil, fmt.Errorf("Fibonacci: argument is not a number")
	}

	n := int(num)
	if n <= 0 {
		return nil, fmt.Errorf("Fibonacci: n must be a positive integer")
	}
	if n == 1 || n == 2 {
		return 1, nil
	}

	a, err := Fibonacci([]interface{}{float64(n - 1)})
	if err != nil {
		return nil, err
	}
	b, err := Fibonacci([]interface{}{float64(n - 2)})
	if err != nil {
		return nil, err
	}
	return a.(int) + b.(int), nil
}

func Sum(args []interface{}) (interface{}, error) {
	var sum int

	for i, arg := range args {
		// JSON 中数字默认是 float64，所以需要类型断言
		num, ok := arg.(float64)
		if !ok {
			return nil, fmt.Errorf("argument at index %d is not a number: %v", i, arg)
		}
		sum += int(num)
	}

	return sum, nil
}
