import axios from 'axios'

const API_BASE = '/api'

// 用户信息类型
export interface UserInfo {
  id: number
  email: string
  nickname?: string
  avatar_url?: string
  is_active: boolean
  is_verified: boolean
  created_at?: string
}

// Token 响应类型
interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

// API 响应类型
interface APIResponse {
  success: boolean
  message: string
  data?: any
}

// 获取认证 token
const getAuthToken = () => localStorage.getItem('auth_token')

// 创建 axios 实例
const authAxios = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
authAxios.interceptors.request.use(
  (config) => {
    const token = getAuthToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：处理 401
authAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除本地存储
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
      // 跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  // 注册
  async register(email: string, password: string, nickname?: string): Promise<APIResponse> {
    const response = await authAxios.post('/auth/register', {
      email,
      password,
      nickname
    })
    return response.data
  },

  // 密码登录
  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await authAxios.post('/auth/login', {
      email,
      password
    })
    return response.data
  },

  // 发送验证码
  async sendCode(email: string, purpose: string = 'login'): Promise<APIResponse> {
    const response = await authAxios.post('/auth/send-code', {
      email,
      purpose
    })
    return response.data
  },

  // 验证码登录
  async loginWithCode(email: string, code: string): Promise<TokenResponse> {
    const response = await authAxios.post('/auth/login-with-code', {
      email,
      code
    })
    return response.data
  },

  // 获取当前用户信息
  async getCurrentUser(): Promise<UserInfo> {
    const response = await authAxios.get('/auth/me')
    return response.data
  },

  // 更新用户信息
  async updateProfile(nickname?: string, avatarUrl?: string): Promise<APIResponse> {
    const response = await authAxios.put('/auth/me', {
      nickname,
      avatar_url: avatarUrl
    })
    return response.data
  },

  // 重置密码
  async resetPassword(email: string, code: string, newPassword: string): Promise<APIResponse> {
    const response = await authAxios.post('/auth/reset-password', {
      email,
      code,
      new_password: newPassword
    })
    return response.data
  },

  // 登出
  logout() {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    window.location.href = '/'
  }
}

// 获取本地存储的用户信息
export const getLocalUserInfo = (): UserInfo | null => {
  const userInfo = localStorage.getItem('user_info')
  return userInfo ? JSON.parse(userInfo) : null
}

// 检查是否已登录
export const isLoggedIn = (): boolean => {
  return !!getAuthToken()
}
