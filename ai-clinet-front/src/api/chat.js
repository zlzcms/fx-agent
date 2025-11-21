import axios from 'axios'

// 获取所有聊天会话（支持分页）
export const getChats = (params = {}) => {
  const { page = 1, size = 20 } = params
  return axios.get('/home/chat/gets', {
    params: { page, size }
  })
}

// 创建聊天会话
export const createChat = data => {
  return axios.post('/home/chat/create', data)
}

// 删除聊天会话
export const deleteChat = chatId => {
  return axios.delete(`/home/chat/delete/${chatId}`)
}

// 获取聊天消息（支持分页）
export const getChatMessages = (chatId, params = {}) => {
  const { page = 1, size = 20 } = params
  return axios.get(`/home/chat/get/${chatId}/messages`, {
    params: { page, size }
  })
}

// 发送消息并获取AI回复
export const sendMessage = params => {
  return axios.post('/home/chat/completion', { ...params })
}
// 打断ai响应
export const interrupAssistant = chat_id => {
  return axios.post(`/home/chat/interrupt/${chat_id}`)
}

// 获取模型列表
export const getModels = () => {
  return axios.get('/home/chat/models')
}
