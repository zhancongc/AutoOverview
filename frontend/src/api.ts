import axios from 'axios';
import type {
  GenerateResponse,
  RecordsResponse,
  ReviewRecord,
  ThreeCirclesResponse,
  ClassifyTopicResponse,
  SmartAnalyzeResponse,
  ResearchDirectionsResponse
} from './types';

// API 基础地址配置
// 开发环境：使用本地代理
// 生产环境：使用相对路径，由 Caddy/Nginx 反向代理到后端
const getApiBase = () => {
  return '/api';
};

const API_BASE = getApiBase();

// 创建 axios 实例并添加拦截器
const apiAxios = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器：添加 token
apiAxios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器：处理 401
apiAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除本地存储
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      // 跳转到登录页
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 异步任务类型
export interface TaskSubmitResponse {
  success: boolean;
  message: string;
  data?: {
    task_id: string;
    topic: string;
    status: string;
    poll_url: string;
  };
}

export interface CreditLogEntry {
  id: number;
  change: number;
  balance_before: number;
  balance_after: number;
  reason: string;
  detail: string | null;
  created_at: string | null;
}

export interface TaskInfo {
  task_id: string;
  topic: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  progress?: {
    step: string;
    message: string;
    papers?: Array<{
      id: string;
      title: string;
      authors: string[];
      year: number | null;
      cited_by_count: number;
      abstract: string | null;
      doi: string | null;
      is_english: boolean;
    }>;
    papers_count?: number;
  };
  result?: any;
  has_result: boolean;
}

export const api = {
  // 智能分析（推荐）
  async smartAnalyze(topic: string): Promise<SmartAnalyzeResponse> {
    const response = await apiAxios.post('/smart-analyze', { topic });
    return response.data;
  },

  // 题目分类
  async classifyTopic(topic: string): Promise<ClassifyTopicResponse> {
    const response = await apiAxios.post('/classify-topic', { topic });
    return response.data;
  },

  // 普通综述生成
  async generateReview(
    topic: string,
    options: {
      targetCount?: number;
      recentYearsRatio?: number;
      englishRatio?: number;
    } = {}
  ): Promise<GenerateResponse> {
    const response = await apiAxios.post('/generate', {
      topic,
      target_count: options.targetCount ?? 50,
      recent_years_ratio: options.recentYearsRatio ?? 0.5,
      english_ratio: options.englishRatio ?? 0.3
    });
    return response.data;
  },

  // 智能生成综述（异步模式）
  async submitReviewTask(
    topic: string,
    options: {
      researchDirectionId?: string;
      language?: string;
      targetCount?: number;
      recentYearsRatio?: number;
      englishRatio?: number;
      searchYears?: number;
      maxSearchQueries?: number;
      reuseTaskId?: string;
    } = {}
  ): Promise<TaskSubmitResponse> {
    const response = await apiAxios.post('/smart-generate', {
      topic,
      research_direction_id: options.researchDirectionId ?? '',
      language: options.language ?? 'zh',
      target_count: options.targetCount ?? 50,
      recent_years_ratio: options.recentYearsRatio ?? 0.5,
      english_ratio: options.englishRatio ?? 0.3,
      search_years: options.searchYears ?? 10,
      max_search_queries: options.maxSearchQueries ?? 8,
      reuse_task_id: options.reuseTaskId ?? ''
    });
    return response.data;
  },

  // 查找文献（不生成综述）
  async searchPapersOnly(
    topic: string,
    options: {
      targetCount?: number;
      searchYears?: number;
    } = {}
  ): Promise<{ success: boolean; message: string; data: any }> {
    const response = await apiAxios.post('/search-papers-only', {
      topic,
      target_count: options.targetCount ?? 50,
      search_years: options.searchYears ?? 10
    }, {
      timeout: 120000  // 2 minutes — LLM-driven search takes 30-60s
    });
    return response.data;
  },

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<{ success: boolean; data: TaskInfo }> {
    const response = await apiAxios.get(`/tasks/${taskId}`);
    return response.data;
  },

  // 通过 task_id 获取综述结果
  async getTaskReview(taskId: string, format: string = 'ieee'): Promise<{ success: boolean; data: {
    task_id: string;
    topic: string;
    review: string;
    papers: any[];
    cited_papers_count: number;
    created_at: string;
    statistics: any;
    record_id?: number;
    is_public: boolean;
    is_paid: boolean;
    duration_seconds?: number;
  } }> {
    const response = await apiAxios.get(`/tasks/${taskId}/review`, {
      params: { format }
    });
    return response.data;
  },

  // 通过 record_id 获取综述结果（支持引用格式切换）
  async getRecordReview(recordId: number, format: string = 'ieee'): Promise<{ success: boolean; data: {
    task_id: string | null;
    topic: string;
    review: string;
    papers: any[];
    cited_papers_count: number;
    created_at: string;
    statistics: any;
    record_id: number;
    is_public: boolean;
    is_paid: boolean;
    duration_seconds?: number;
  } }> {
    const response = await apiAxios.get(`/records/${recordId}/review`, {
      params: { format }
    });
    return response.data;
  },

  // 三圈分析
  async analyzeThreeCircles(topic: string): Promise<ThreeCirclesResponse> {
    const response = await apiAxios.post('/analyze-three-circles', { topic });
    return response.data;
  },

  // 三圈综述生成
  async generateThreeCirclesReview(
    topic: string,
    options: {
      targetCount?: number;
      recentYearsRatio?: number;
      englishRatio?: number;
    } = {}
  ): Promise<GenerateResponse> {
    const response = await apiAxios.post('/generate-three-circles', {
      topic,
      target_count: options.targetCount ?? 50,
      recent_years_ratio: options.recentYearsRatio ?? 0.5,
      english_ratio: options.englishRatio ?? 0.3
    });
    return response.data;
  },

  // 历史记录
  async getRecords(skip: number = 0, limit: number = 20): Promise<RecordsResponse> {
    const response = await apiAxios.get('/records', {
      params: { skip, limit }
    });
    return response.data;
  },

  async getRecord(id: number): Promise<{ success: boolean; record: ReviewRecord }> {
    const response = await apiAxios.get(`/records/${id}`);
    return response.data;
  },

  async deleteRecord(id: number): Promise<{ success: boolean; message: string }> {
    const response = await apiAxios.delete(`/records/${id}`);
    return response.data;
  },

  // 导出综述为 Word
  async exportReview(recordId: number): Promise<Blob> {
    const response = await apiAxios.post('/records/export', {
      record_id: recordId
    }, {
      responseType: 'blob'
    });
    return response.data;
  },

  // 单次解锁综述（29.8元）
  async unlockRecord(recordId: number): Promise<{ success: boolean; message: string; order_no?: string; pay_url?: string; already_unlocked?: boolean }> {
    const response = await apiAxios.post('/records/unlock', {
      record_id: recordId
    });
    return response.data;
  },

  // 使用积分解锁综述（扣除1个付费积分）
  async unlockRecordWithCredit(recordId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiAxios.post('/records/unlock-with-credit', {
      record_id: recordId
    });
    return response.data;
  },

  // 健康检查
  async checkHealth(): Promise<{ status: string; deepseek_configured: boolean }> {
    const response = await apiAxios.get('/health');
    return response.data;
  },

  // 获取研究方向列表
  async getResearchDirections(): Promise<ResearchDirectionsResponse> {
    const response = await apiAxios.get('/research-directions');
    return response.data;
  },

  // ==================== 订阅/支付 API ====================

  async getSubscriptionPlans(): Promise<{ plans: Array<{
    type: string;
    name: string;
    name_en: string;
    price: number;
    price_usd: number;
    original_price?: number;
    original_price_usd?: number;
    credits: number;
    credits_cn?: number;
    recommended?: boolean;
    features: string[];
    features_en: string[];
    badge?: string;
    badge_en?: string;
  }> }> {
    const response = await apiAxios.get('/subscription/plans');
    return response.data;
  },

  async createSubscription(planType: string): Promise<{
    order_no: string;
    pay_url: string;
    amount: number;
  }> {
    const response = await apiAxios.post('/subscription/create', {
      plan_type: planType
    });
    return response.data;
  },

  async querySubscription(orderNo: string): Promise<{
    status: string;
    payment_time?: string;
    expires_at?: string;
  }> {
    const response = await apiAxios.get(`/subscription/query/${orderNo}`);
    return response.data;
  },

  async getMembershipInfo(): Promise<{
    membership_type: string;
    expires_at?: string;
    days_remaining?: number;
  }> {
    const response = await apiAxios.get('/subscription/membership');
    return response.data;
  },

  async getCredits(): Promise<{ credits: number; free_credits: number; has_purchased: boolean }> {
    const response = await apiAxios.get('/usage/credits');
    return response.data;
  },

  async getCreditLogs(limit = 50, offset = 0): Promise<{ total: number; logs: CreditLogEntry[] }> {
    const response = await apiAxios.get('/credit-logs', { params: { limit, offset } });
    return response.data;
  },

  async getSearchDailyLimit(): Promise<{ limit: number; used: number; remaining: number; bonus: number; next_reset_at: number | null }> {
    const response = await apiAxios.get('/search/daily-limit');
    return response.data;
  },

  async submitFeedback(data: { email: string; content: string }): Promise<{ success: boolean }> {
    const response = await apiAxios.post('/feedback', data);
    return response.data;
  },

  async checkJadeAccess(): Promise<{ allowed: boolean }> {
    const response = await apiAxios.get('/jade/access');
    return response.data;
  },

  async getActiveTask(): Promise<{ active: boolean; task_id?: string; topic?: string; status?: string }> {
    const response = await apiAxios.get('/tasks/active');
    return response.data;
  },

  // 获取搜索历史
  async getSearchHistory(skip: number = 0, limit: number = 20): Promise<{
    success: boolean;
    count: number;
    searches: Array<{
      id: string;
      topic: string;
      user_id?: number;
      status: string;
      current_stage?: string;
      params: any;
      created_at: string;
      papers_summary?: any;
      papers_count?: number;
      papers_sample?: any[];
    }>;
  }> {
    const response = await apiAxios.get('/search-history', {
      params: { skip, limit }
    });
    return response.data;
  },

  // 获取搜索历史详情
  async getSearchHistoryDetail(taskId: string): Promise<{
    success: boolean;
    search: any;
  }> {
    const response = await apiAxios.get(`/search-history/${taskId}`);
    return response.data;
  },

  // ==================== Paddle Payment API (International) ====================

  async getPaddlePlans(): Promise<{ plans: Record<string, {
    name: string;
    price: number;
    credits: number;
    currency: string;
  }> }> {
    const response = await apiAxios.get('/paddle/plans');
    return response.data;
  },

  async createPaddleSubscription(planType: string): Promise<{
    order_no: string;
    checkout_url: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.post('/paddle/create', {
      plan_type: planType
    });
    return response.data;
  },

  async queryPaddleSubscription(orderNo: string): Promise<{
    status: string;
    payment_time?: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.get(`/paddle/query/${orderNo}`);
    return response.data;
  },

  async createPaddleUnlock(recordId: number): Promise<{
    order_no: string;
    checkout_url: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.post('/paddle/unlock', {
      record_id: recordId
    });
    return response.data;
  },

  // ==================== PayPal Payment API (International Default) ====================

  async getPayPalConfig(): Promise<{ client_id: string; sandbox: boolean }> {
    const response = await apiAxios.get('/paypal/config');
    return response.data;
  },

  async createPayPalSubscription(planType: string): Promise<{
    order_no: string;
    paypal_order_id: string;
    approval_link: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.post('/paypal/create', {
      plan_type: planType
    });
    return response.data;
  },

  async capturePayPalOrder(paypalOrderId: string): Promise<{
    status: string;
    order_no: string;
    payment_time?: string;
  }> {
    const response = await apiAxios.post('/paypal/capture', {
      order_id: paypalOrderId
    });
    return response.data;
  },

  async queryPayPalSubscription(orderNo: string): Promise<{
    status: string;
    payment_time?: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.get(`/paypal/query/${orderNo}`);
    return response.data;
  },

  async createPayPalUnlock(recordId: number): Promise<{
    order_no: string;
    paypal_order_id: string;
    approval_link: string;
    amount: number;
    currency: string;
  }> {
    const response = await apiAxios.post('/paypal/unlock', {
      record_id: recordId
    });
    return response.data;
  },

  // ==================== 对比矩阵 API ====================

  // 提交对比矩阵生成任务
  async generateComparisonMatrix(
    topic: string,
    options: {
      reuseTaskId?: string;
      language?: string;
    } = {}
  ): Promise<TaskSubmitResponse> {
    const response = await apiAxios.post('/generate-comparison-matrix', {
      topic,
      reuse_task_id: options.reuseTaskId ?? '',
      language: options.language ?? 'zh'
    });
    return response.data;
  },

  // 获取对比矩阵结果
  async getComparisonMatrix(taskId: string): Promise<{
    success: boolean;
    data: {
      task_id: string;
      topic: string;
      comparison_matrix: string;
      statistics: {
        papers_used: number;
        total_time_seconds: number;
        generated_at: string;
      };
      papers: any[];
    };
  }> {
    const response = await apiAxios.get(`/comparison-matrix/${taskId}`);
    return response.data;
  },

  // 查询搜索任务的关联任务（对比矩阵、综述）
  async getRelatedTasks(taskId: string): Promise<{
    success: boolean;
    data: Array<{
      task_id: string;
      topic: string;
      status: string;
      type: 'comparison_matrix' | 'review';
      created_at: string;
    }>;
  }> {
    const response = await apiAxios.get(`/search-history/${taskId}/related-tasks`);
    return response.data;
  },

  async shareSearchResult(taskId: string): Promise<{ success: boolean; data: { task_id: string; is_public: boolean } }> {
    const response = await apiAxios.post(`/tasks/${taskId}/share`, {});
    return response.data;
  },

  async getSharedPapers(taskId: string): Promise<{ success: boolean; data: { task_id: string; topic: string; papers: any[]; statistics: any } }> {
    const response = await apiAxios.get(`/tasks/${taskId}/shared-papers`);
    return response.data;
  },

  // ==================== 分享奖励 API ====================

  async uploadShareProof(taskId: string, image: File): Promise<{ success: boolean; message?: string; credits?: number }> {
    const formData = new FormData();
    formData.append('task_id', taskId);
    formData.append('image', image);
    const response = await apiAxios.post('/share-reward', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getShareRewardStatus(): Promise<{ success: boolean; claimed: boolean }> {
    const response = await apiAxios.get('/share-reward/status', {
      params: { task_id: 'check' }
    });
    return response.data;
  },
};
