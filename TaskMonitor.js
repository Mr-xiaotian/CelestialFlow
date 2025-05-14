import { useState, useEffect } from "react";

// 模拟后端数据
const mockTreeStructure = [
  "+---------------------------------------------------------------+",
  "| RootStage (stage_mode: process, func: process_task)           |",
  "| ╘--> Splitter (stage_mode: process, func: split_task)         |",
  "|   ╘--> Processor (stage_mode: process, func: process_item)    |",
  "|     ╘--> Validator (stage_mode: process, func: validate_item) |",
  "+---------------------------------------------------------------+"
];

// 模拟节点状态数据
const initialNodeStatuses = {
  "RootStage": { 
    active: true, 
    tasks_processed: 45, 
    tasks_pending: 12, 
    tasks_error: 3,
    start_time: "2025-05-14T10:15:32",
    execution_mode: "thread"
  },
  "Splitter": { 
    active: true, 
    tasks_processed: 42, 
    tasks_pending: 15, 
    tasks_error: 0,
    start_time: "2025-05-14T10:15:33",
    execution_mode: "thread"
  },
  "Processor": { 
    active: true, 
    tasks_processed: 150, 
    tasks_pending: 30, 
    tasks_error: 5,
    start_time: "2025-05-14T10:15:34",
    execution_mode: "thread"
  },
  "Validator": { 
    active: true, 
    tasks_processed: 145, 
    tasks_pending: 5, 
    tasks_error: 0,
    start_time: "2025-05-14T10:15:35",
    execution_mode: "thread"
  }
};

// 模拟错误数据
const initialErrors = [
  { 
    error: "TaskError(Could not process task)",
    node: "RootStage",
    task_id: "task_001",
    timestamp: "2025-05-14T10:16:12"
  },
  { 
    error: "TaskError(Invalid input format)",
    node: "RootStage",
    task_id: "task_015",
    timestamp: "2025-05-14T10:17:45" 
  },
  { 
    error: "TaskError(Process timeout)",
    node: "Processor",
    task_id: "task_023_split_1",
    timestamp: "2025-05-14T10:18:02" 
  }
];

export default function TaskMonitor() {
  const [selectedTab, setSelectedTab] = useState("dashboard");
  const [nodeStatuses, setNodeStatuses] = useState(initialNodeStatuses);
  const [errors, setErrors] = useState(initialErrors);
  const [treeStructure, setTreeStructure] = useState(mockTreeStructure);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isRunning, setIsRunning] = useState(true);
  const [refreshRate, setRefreshRate] = useState(5);
  
  // 模拟数据刷新
  useEffect(() => {
    if (!isRunning) return;
    
    const timer = setInterval(() => {
      // 更新节点状态数据
      setNodeStatuses(prev => {
        const updated = {...prev};
        Object.keys(updated).forEach(node => {
          const randomIncrement = Math.floor(Math.random() * 5);
          if (updated[node].tasks_pending > 0) {
            updated[node].tasks_processed += randomIncrement;
            updated[node].tasks_pending = Math.max(0, updated[node].tasks_pending - randomIncrement);
          }
          
          // 随机添加错误
          if (Math.random() > 0.9 && node === "Processor") {
            updated[node].tasks_error += 1;
            
            // 添加新错误到错误列表
            setErrors(prev => [...prev, {
              error: "TaskError(New random error)",
              node: node,
              task_id: `task_${Math.floor(Math.random() * 1000)}`,
              timestamp: new Date().toISOString()
            }]);
          }
        });
        return updated;
      });
    }, refreshRate * 1000);
    
    return () => clearInterval(timer);
  }, [isRunning, refreshRate]);
  
  // 按节点过滤错误
  const filteredErrors = selectedNode 
    ? errors.filter(error => error.node === selectedNode)
    : errors;
  
  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* 标题栏 */}
      <div className="bg-blue-600 text-white p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">任务树监控系统</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="mr-2">刷新间隔:</span>
              <select 
                value={refreshRate}
                onChange={(e) => setRefreshRate(Number(e.target.value))}
                className="bg-blue-700 text-white p-1 rounded"
              >
                <option value={1}>1秒</option>
                <option value={5}>5秒</option>
                <option value={10}>10秒</option>
                <option value={30}>30秒</option>
              </select>
            </div>
            <button 
              onClick={() => setIsRunning(!isRunning)}
              className={`px-3 py-1 rounded ${isRunning ? 'bg-red-500' : 'bg-green-500'}`}
            >
              {isRunning ? '暂停刷新' : '开始刷新'}
            </button>
          </div>
        </div>
      </div>
      
      {/* 导航栏 */}
      <div className="bg-gray-800 text-white flex">
        <button 
          className={`px-6 py-3 ${selectedTab === 'dashboard' ? 'bg-gray-700 border-b-2 border-blue-500' : ''}`}
          onClick={() => setSelectedTab('dashboard')}
        >
          仪表盘
        </button>
        <button 
          className={`px-6 py-3 ${selectedTab === 'structure' ? 'bg-gray-700 border-b-2 border-blue-500' : ''}`}
          onClick={() => setSelectedTab('structure')}
        >
          任务树结构
        </button>
        <button 
          className={`px-6 py-3 ${selectedTab === 'errors' ? 'bg-gray-700 border-b-2 border-blue-500' : ''}`}
          onClick={() => setSelectedTab('errors')}
        >
          错误日志
        </button>
      </div>
      
      {/* 内容区域 */}
      <div className="flex-1 p-4 overflow-auto">
        {selectedTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 节点状态卡片 */}
            {Object.entries(nodeStatuses).map(([nodeName, status]) => (
              <div 
                key={nodeName}
                className={`rounded-lg shadow-md p-4 ${status.active ? 'bg-white' : 'bg-gray-200'}`}
              >
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-xl font-semibold">{nodeName}</h3>
                  <span className={`px-2 py-1 rounded text-white text-sm ${status.active ? 'bg-green-500' : 'bg-gray-500'}`}>
                    {status.active ? '运行中' : '已停止'}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-gray-600 text-sm">已处理任务</div>
                    <div className="text-lg font-bold">{status.tasks_processed}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-sm">等待任务</div>
                    <div className="text-lg font-bold">{status.tasks_pending}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-sm">错误任务</div>
                    <div className="text-lg font-bold text-red-600">{status.tasks_error}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 text-sm">执行模式</div>
                    <div className="text-lg font-bold">{status.execution_mode}</div>
                  </div>
                </div>
                
                <div className="text-sm text-gray-500">
                  开始时间: {new Date(status.start_time).toLocaleString()}
                </div>
                
                {/* 进度条 */}
                <div className="mt-3">
                  <div className="mb-1 flex justify-between">
                    <span className="text-sm">任务完成率</span>
                    <span className="text-sm">
                      {Math.round(status.tasks_processed / (status.tasks_processed + status.tasks_pending) * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 rounded-full h-2" 
                      style={{width: `${Math.round(status.tasks_processed / (status.tasks_processed + status.tasks_pending) * 100)}%`}}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* 总体状态摘要 */}
            <div className="md:col-span-2 bg-white rounded-lg shadow-md p-4 mt-4">
              <h3 className="text-xl font-semibold mb-4">总体状态摘要</h3>
              
              <div className="grid grid-cols-4 gap-6">
                <div className="rounded bg-blue-100 p-4 text-center">
                  <div className="text-3xl font-bold text-blue-700">
                    {Object.values(nodeStatuses).reduce((sum, node) => sum + node.tasks_processed, 0)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">总处理任务</div>
                </div>
                
                <div className="rounded bg-yellow-100 p-4 text-center">
                  <div className="text-3xl font-bold text-yellow-700">
                    {Object.values(nodeStatuses).reduce((sum, node) => sum + node.tasks_pending, 0)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">总等待任务</div>
                </div>
                
                <div className="rounded bg-red-100 p-4 text-center">
                  <div className="text-3xl font-bold text-red-700">
                    {Object.values(nodeStatuses).reduce((sum, node) => sum + node.tasks_error, 0)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">总错误任务</div>
                </div>
                
                <div className="rounded bg-green-100 p-4 text-center">
                  <div className="text-3xl font-bold text-green-700">
                    {Object.keys(nodeStatuses).length}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">活动节点</div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {selectedTab === 'structure' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">任务树结构</h2>
            <div className="bg-gray-100 p-4 rounded font-mono whitespace-pre overflow-x-auto">
              {treeStructure.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          </div>
        )}
        
        {selectedTab === 'errors' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">错误日志</h2>
              <div className="flex items-center">
                <span className="mr-2">按节点筛选:</span>
                <select 
                  className="border p-1 rounded"
                  value={selectedNode || ''}
                  onChange={(e) => setSelectedNode(e.target.value || null)}
                >
                  <option value="">全部节点</option>
                  {Object.keys(nodeStatuses).map(node => (
                    <option key={node} value={node}>{node}</option>
                  ))}
                </select>
              </div>
            </div>
            
            {filteredErrors.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">错误信息</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">节点</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">任务ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredErrors.map((error, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-red-500 font-mono">{error.error}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{error.node}</td>
                        <td className="px-6 py-4 whitespace-nowrap font-mono">{error.task_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                          {new Date(error.timestamp).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500">没有找到错误记录</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}