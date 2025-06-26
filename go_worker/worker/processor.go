package worker

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
)

// Add100 接收一个整数参数，返回该整数加 100
func Add100(args []any) (any, error) {
	if len(args) != 1 {
		return nil, fmt.Errorf("Add100 expects 1 argument, got %d", len(args))
	}

	num, ok := args[0].(float64) // JSON 解析为 float64
	if !ok {
		return nil, fmt.Errorf("argument is not a number")
	}

	return int(num) + 100, nil
}

// Fibonacci 计算第 n 个斐波那契数（递归版）
func Fibonacci(args []any) (any, error) {
	if len(args) != 1 {
		return nil, fmt.Errorf("Fibonacci expects 1 argument, got %d", len(args))
	}

	num, ok := args[0].(float64)
	if !ok {
		return nil, fmt.Errorf("argument is not a number")
	}

	n := int(num)
	if n <= 0 {
		return nil, fmt.Errorf("n must be a positive integer")
	}
	if n == 1 || n == 2 {
		return 1, nil
	}

	a, err := Fibonacci([]any{float64(n - 1)})
	if err != nil {
		return nil, err
	}
	b, err := Fibonacci([]any{float64(n - 2)})
	if err != nil {
		return nil, err
	}
	return a.(int) + b.(int), nil
}

func Sum(args []any) (any, error) {
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

// DownloadToFile 下载指定 URL 内容并保存到指定本地文件路径
func DownloadToFile(args []any) (any, error) {
	if len(args) != 2 {
		return nil, fmt.Errorf("DownloadToFile expects 2 arguments, got %d", len(args))
	}

	// 类型断言为 string
	url, ok1 := args[0].(string)
	path, ok2 := args[1].(string)

	if !ok1 || !ok2 {
		return nil, errors.New("both arguments must be strings")
	}

	// 发送 HTTP GET 请求
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %v", err)
	}
	defer resp.Body.Close()

	// 检查响应码
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP error: status code %d", resp.StatusCode)
	}

	// 创建目标文件
	file, err := os.Create(path)
	if err != nil {
		return nil, fmt.Errorf("file creation failed: %v", err)
	}
	defer file.Close()

	// 将响应内容复制到文件
	_, err = io.Copy(file, resp.Body)
	if err != nil {
		return nil, fmt.Errorf("file write failed: %v", err)
	}

	return "Downloaded success", nil
}
