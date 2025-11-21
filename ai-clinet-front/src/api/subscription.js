import axios from 'axios'

// 获取用户订阅列表
export const getUserSubscriptions = () => {
  return axios.get('/home/ai/subscriptions')
}

// 标记已读报告
export const markReadReport = report_id => {
  return axios.post(`/home/ai/reports/${report_id}/read`)
}

// 获取订阅的已生成的报告列表
export const getUserReports = params => {
  return axios.get('/home/ai/reports', { params: { ...params } })
}

// 获取ai助理列表
export const getAiAssistants = () => {
  return axios.get('/home/ai/assistants/all')
}