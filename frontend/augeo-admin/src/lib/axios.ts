import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
})

// Request interceptor to add Authorization header
apiClient.interceptors.request.use(
  (config) => {
    // Get access token from auth store
    const token = useAuthStore.getState().accessToken

    // Add Authorization header if token exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    // Return successful responses as-is
    return response
  },
  (error) => {
    // Handle 401 Unauthorized - clear auth and redirect to login
    if (error.response?.status === 401) {
      useAuthStore.getState().reset()

      // Only redirect if not already on auth pages
      if (!window.location.pathname.startsWith('/sign-in')) {
        window.location.href = '/sign-in'
      }
    }

    // Handle 429 Too Many Requests - extract retry-after if available
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after']
      if (retryAfter) {
        error.retryAfter = parseInt(retryAfter, 10)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
