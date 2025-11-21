import axios from 'axios'

// 获取当前用户的推荐问法
export const getRecommendedQuestions = (limit = 3) => {
  return axios.get('/sys/recommended-questions/for-current-user', {
    params: {
      limit: parseInt(limit, 10)
    }
  })
}
