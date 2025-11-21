import axios from 'axios'

export const register = userData => {
  return axios.post('/home/auth/register', userData)
}

export const login = credentials => {
  const formData = new FormData()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)
  return axios.post('/home/auth/login', formData)
}

export const refreshToken = refreshToken => {
  return axios.post('/home/auth/refresh-token', { refresh_token: refreshToken })
}

export const getUserInfo = () => {
  return axios.get('/home/auth/me')
}

export const updateUserProfile = userData => {
  return axios.put('/home/auth/me', userData)
}
