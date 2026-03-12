import axios from 'axios'

// Unified API configuration - works for both development and production
const api = axios.create({
  baseURL: '/api',  // Always use relative path since backend serves frontend
  timeout: 30000,   // 30 second timeout for video analysis
})

export const setToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
    localStorage.setItem('token', token)
  } else {
    delete api.defaults.headers.common.Authorization
    localStorage.removeItem('token')
  }
}

// Auto-load stored token
const storedToken = localStorage.getItem('token')
if (storedToken) {
  setToken(storedToken)
}

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      setToken(null)
      window.location.href = '/auth'
    }
    return Promise.reject(error)
  }
)

export default api
