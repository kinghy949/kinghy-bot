import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

/** 提交生成任务 */
export function submitGenerate(data) {
  return api.post('/generate', data)
}

/** 查询任务状态 */
export function getTaskState(taskId) {
  return api.get(`/task/${taskId}`)
}

/** 获取可用技术栈列表 */
export function getTechStacks() {
  return api.get('/tech-stacks')
}

/** 取消任务 */
export function cancelTask(taskId) {
  return api.post(`/task/${taskId}/cancel`)
}

/** 下载链接 */
export function getDownloadUrl(taskId, docType) {
  return `/api/download/${taskId}/${docType}`
}

/** 创建SSE连接 */
export function createTaskStream(taskId, onMessage, onError) {
  const eventSource = new EventSource(`/api/task/${taskId}/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
      if (data.status === 'completed' || data.status === 'failed') {
        eventSource.close()
      }
    } catch (e) {
      console.error('SSE解析错误:', e)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    if (onError) onError()
  }

  return eventSource
}

export default api
