import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { isLoggedIn as checkLoggedIn, getLocalUserInfo, authApi } from '../authApi'
import { LoginModal } from './LoginModal'
import { PaymentModal } from './PaymentModal'
import './SimpleApp.css'

interface TaskProgress {
  step: string
  message: string
}

export function SimpleApp() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [error, setError] = useState('')
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState<string | false>(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)

  useEffect(() => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (loggedIn) {
      setUserInfo(getLocalUserInfo())
    }
  }, [])

  useEffect(() => {
    const pendingTopic = sessionStorage.getItem('pending_topic')
    if (pendingTopic) {
      sessionStorage.removeItem('pending_topic')
      setTopic(pendingTopic)
    }
  }, [])

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('\u8BF7\u8F93\u5165\u7814\u7A76\u4E3B\u9898')
      return
    }

    if (!checkLoggedIn()) {
      setShowLoginModal(true)
      return
    }

    setIsGenerating(true)
    setProgress({ step: 'init', message: '\u6B63\u5728\u63D0\u4EA4\u4EFB\u52A1...' })
    setError('')

    try {
      const submitResponse = await api.submitReviewTask(topic, {
        targetCount: 50,
        recentYearsRatio: 0.5,
        englishRatio: 0.3,
        searchYears: 10,
        maxSearchQueries: 8
      })

      if (!submitResponse.success || !submitResponse.data?.task_id) {
        if (submitResponse.message?.includes('额度已用完')) {
          setError(submitResponse.message)
          setShowPaymentModal('single')
        } else {
          setError(submitResponse.message || '\u4EFB\u52A1\u63D0\u4EA4\u5931\u8D25')
        }
        setIsGenerating(false)
        return
      }

      const taskId = submitResponse.data.task_id
      const startTime = Date.now()
      let pollCount = 0

      const doPoll = async () => {
        try {
          const statusResponse = await api.getTaskStatus(taskId)

          if (!statusResponse.success) {
            setError('\u67E5\u8BE2\u4EFB\u52A1\u72B6\u6001\u5931\u8D25')
            setIsGenerating(false)
            return
          }

          const taskInfo = statusResponse.data

          const elapsedMinutes = (Date.now() - startTime) / 1000 / 60
          let expectedRemainingMinutes = Math.max(0, Math.round(5 - elapsedMinutes))

          let progressMessage = taskInfo.progress?.message || '\u6B63\u5728\u5904\u7406...'
          if (expectedRemainingMinutes > 0) {
            progressMessage += `\uFF08\u9884\u671F\u8FD8\u6709${expectedRemainingMinutes}\u5206\u949F\uFF09`
          }

          setProgress({
            step: taskInfo.progress?.step || 'processing',
            message: progressMessage
          })

          if (taskInfo.status === 'completed' && taskInfo.result) {
            setProgress({ step: 'completed', message: '\u751F\u6210\u5B8C\u6210\uFF01\u6B63\u5728\u8DF3\u8F6C...' })
            setTimeout(() => {
              navigate(`/review?task_id=${taskId}`)
            }, 500)
            return
          } else if (taskInfo.status === 'failed') {
            setError(taskInfo.error || '\u4EFB\u52A1\u6267\u884C\u5931\u8D25')
            setIsGenerating(false)
            return
          }

          pollCount++
          const elapsed = Date.now() - startTime
          const nextInterval = elapsed < 2 * 60 * 1000 ? 15000 : 5000
          setTimeout(doPoll, nextInterval)
        } catch (err) {
          setError('\u67E5\u8BE2\u4EFB\u52A1\u72B6\u6001\u51FA\u9519')
          setIsGenerating(false)
          console.error(err)
        }
      }

      setTimeout(doPoll, 1000)
    } catch (err) {
      setError('\u63D0\u4EA4\u4EFB\u52A1\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u540E\u7AEF\u670D\u52A1\u662F\u5426\u6B63\u5E38\u8FD0\u884C')
      setIsGenerating(false)
      console.error(err)
    }
  }

  const handleLoginSuccess = () => {
    const loggedIn = checkLoggedIn()
    setIsLoggedIn(loggedIn)
    if (loggedIn) {
      setUserInfo(getLocalUserInfo())
    }
    setShowLoginModal(false)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    setIsLoggedIn(false)
    setUserInfo(null)
  }

  const getProgressPercentage = () => {
    if (!progress) return 0
    switch (progress.step) {
      case 'init': return 5
      case 'waiting': return 5
      case 'generating_outline': return 15
      case 'analyzing': return 20
      case 'optimizing_keywords': return 25
      case 'searching': return 40
      case 'filtering': return 60
      case 'topic_relevance_check': return 65
      case 'generating': return 80
      case 'validating': return 90
      case 'completed': return 100
      default: return 5
    }
  }

  return (
    <div className="simple-home">
      <nav className="home-nav">
        <div className="nav-logo">
          <span className="logo-icon">📚</span>
          <span className="logo-text">AutoOverview</span>
        </div>
        <div className="nav-links">
          <a href="#features">产品特色</a>
          <a href="#process">使用流程</a>
          <a href="#cases">案例展示</a>
          <a href="#pricing">价格方案</a>
        </div>
        <div className="nav-actions">
          {isLoggedIn ? (
            <div className="user-menu">
              <button className="user-info" onClick={() => navigate('/profile')}>
                <span className="user-avatar">👤</span>
                <span className="user-name">{userInfo?.nickname || '用户'}</span>
              </button>
              <button className="nav-btn nav-btn-logout" onClick={handleLogout}>
                退出
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button className="nav-btn nav-btn-login" onClick={() => setShowLoginModal(true)}>
                登录
              </button>
              <button
                className="nav-btn nav-btn-register"
                onClick={() => setShowLoginModal(true)}
              >
                注册
              </button>
            </div>
          )}
        </div>
      </nav>

      <div className="home-container">
        <div className="home-hero-wrapper">
          <div className="home-hero">
            <span className="hero-accent">学术研究 · 高效利器</span>
            <h1 className="home-title">
              让综述编写<span className="highlight">简单到只需一句话</span>
            </h1>
            <p className="home-subtitle">
              输入研究主题，一键生成专业文献综述。让 AI 助您在学术道路上更进一步。
            </p>
          </div>

          <div className="hero-visual">
            <div className="visual-card">
              <div className="visual-icon-large">🔬</div>
              <div className="visual-stats">
                <div className="visual-stat">
                  <span className="visual-stat-number">权威</span>
                  <span className="visual-stat-label">- 学术期刊</span>
                </div>
                <div className="visual-stat">
                  <span className="visual-stat-number">海量</span>
                  <span className="visual-stat-label">- 论文数据</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="home-input-section">
          <div className="input-section-header">
            <h2 className="input-section-title">一键生成论文综述</h2>
            <p className="input-section-subtitle">输入研究主题，AI 为您生成专业文献综述</p>
          </div>

          <input
            type="text"
            className="home-input"
            placeholder="请输入您的研究主题，例如：深度学习在图像识别中的应用"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isGenerating && handleGenerate()}
            disabled={isGenerating}
          />

          <button
            className="home-button"
            onClick={handleGenerate}
            disabled={isGenerating || !topic.trim()}
          >
            {isGenerating ? '生成中...' : '生成综述'}
          </button>

          {error && (
            <div className="home-error">
              {error}
            </div>
          )}

          {isGenerating && progress && (
            <div className="home-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
              <div className="progress-message">{progress.message}</div>
            </div>
          )}
        </div>
      </div>

      <section id="features" className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">为什么选择 AutoOverview？</h2>
          <div className="comparison-grid">
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">🤖</span>
                <h3 className="comparison-card-title">免费大模型</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">❌ 缺乏真实论文数据支撑</li>
                <li className="comparison-item negative">❌ 无法获取最新研究进展</li>
                <li className="comparison-item negative">❌ 可能编造引用文献</li>
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">🔧</span>
                <h3 className="comparison-card-title">Elicit / Scite / Paperpal</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">❌ 功能单一，仅辅助工具</li>
                <li className="comparison-item negative">❌ 无法生成完整综述</li>
                <li className="comparison-item negative">❌ 使用门槛高</li>
              </ul>
            </div>
            <div className="comparison-card highlight">
              <div className="comparison-card-header">
                <span className="comparison-icon">📄</span>
                <h3 className="comparison-card-title">AutoOverview</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item positive">✅ 海量真实学术期刊数据源</li>
                <li className="comparison-item positive">✅ 2分钟遍历文献，5分钟生成综述</li>
                <li className="comparison-item positive">✅ 学术规范，精准引用</li>
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">👤</span>
                <h3 className="comparison-card-title">第三方人工服务</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">❌ 价格昂贵，质量参差不齐</li>
                <li className="comparison-item negative">❌ 耗时数天至数周</li>
                <li className="comparison-item negative">❌ 存在学术合规风险</li>
              </ul>
            </div>
            <div className="comparison-card">
              <div className="comparison-card-header">
                <span className="comparison-icon">📖</span>
                <h3 className="comparison-card-title">知网研学 / 自己写</h3>
              </div>
              <ul className="comparison-list">
                <li className="comparison-item negative">❌ 耗时数周甚至数月</li>
                <li className="comparison-item negative">❌ 查找文献效率低</li>
                <li className="comparison-item negative">❌ 难以全面覆盖前沿</li>
              </ul>
            </div>
          </div>
          <div className="home-features">
            <div className="feature-item">
              <span className="feature-icon">📚</span>
              <div>
                <h3 className="feature-title">海量真实数据</h3>
                <p className="feature-desc">海量、真实、最新的论文数据，帮您掌握前沿进展</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">⚡</span>
              <div>
                <h3 className="feature-title">极速效率</h3>
                <p className="feature-desc">2分钟遍历相关文献，5分钟生成专业综述</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎯</span>
              <div>
                <h3 className="feature-title">专业规范</h3>
                <p className="feature-desc">学术规范的综述结构，精准引用权威文献</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="process" className="landing-section section-alt">
        <div className="section-inner">
          <h2 className="section-title">使用流程</h2>
          <p className="section-subtitle">三步完成专业文献综述</p>
          <div className="process-steps">
            <div className="process-step">
              <div className="step-number">01</div>
              <div className="step-icon">✏️</div>
              <h3 className="step-title">输入主题</h3>
              <p className="step-desc">输入您的研究主题，可以是一句话描述，也可以是详细的研究方向要求。</p>
            </div>
            <div className="process-arrow">→</div>
            <div className="process-step">
              <div className="step-number">02</div>
              <div className="step-icon">✨</div>
              <h3 className="step-title">AI 智能生成</h3>
              <p className="step-desc">AI 自动搜索文献、分析筛选、组织结构、撰写综述，全程自动化处理。</p>
            </div>
            <div className="process-arrow">→</div>
            <div className="process-step">
              <div className="step-number">03</div>
              <div className="step-icon">📄</div>
              <h3 className="step-title">查看与导出</h3>
              <p className="step-desc">在线预览综述内容，支持导出 Word 文档，可直接用于学术写作。</p>
            </div>
          </div>
        </div>
      </section>

      <section id="cases" className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">案例展示</h2>
          <p className="section-subtitle">看看 AI 生成的综述效果</p>
          <div className="cases-grid">
            <div className="case-card" onClick={() => navigate('/review?task_id=c851aa9a')} role="button" tabIndex={0}>
              <div className="case-icon">🧮</div>
              <h3 className="case-title">Computer Algebra System 的算法实现及应用</h3>
              <p className="case-desc">涵盖了计算机代数系统中的多项式运算、符号计算、Groebner 基等核心算法，以及在密码学和机器人学中的应用。</p>
              <div className="case-tags">
                <span className="case-tag">计算机科学</span>
                <span className="case-tag">代数算法</span>
              </div>
            </div>
            <div className="case-card" onClick={() => navigate('/review?task_id=feae8f9d')} role="button" tabIndex={0}>
              <div className="case-icon">🔬</div>
              <h3 className="case-title">光催化杀菌技术的机理、影响因素及应用前景研究</h3>
              <p className="case-desc">系统综述了 TiO₂ 等光催化材料的杀菌机理、影响催化效率的关键因素，以及在医疗卫生、食品保鲜等领域的前沿应用。</p>
              <div className="case-tags">
                <span className="case-tag">材料科学</span>
                <span className="case-tag">光催化</span>
              </div>
            </div>
            <div className="case-card" onClick={() => navigate('/review?task_id=84bba875')} role="button" tabIndex={0}>
              <div className="case-icon">🧠</div>
              <h3 className="case-title">脑机接口在卒中运动康复中的研究进展与临床转化</h3>
              <p className="case-desc">全面梳理了脑机接口技术在卒中患者运动功能康复中的最新研究进展，包括信号解码算法、神经可塑性机制及临床转化挑战。</p>
              <div className="case-tags">
                <span className="case-tag">医学</span>
                <span className="case-tag">脑机接口</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="landing-section section-alt">
        <div className="section-inner">
          <h2 className="section-title">价格方案</h2>
          <p className="section-subtitle">按需购买，注册即送 1 篇免费综述</p>
          <div className="pricing-grid">
            <div className="pricing-card">
              <h3 className="pricing-name">单次体验</h3>
              <div className="pricing-price">
                <span className="pricing-original">{'\u00A539.9'}</span>
                {'\u00A529.8'}
              </div>
              <ul className="pricing-features">
                <li>1 篇综述生成额度</li>
                <li>在线查看 + PDF 导出</li>
                <li>限时优惠，省 {'\u00A510.2'}</li>
              </ul>
              <button className="pricing-btn pricing-btn-primary" onClick={() => { isLoggedIn ? setShowPaymentModal('single') : setShowLoginModal(true) }}>立即购买</button>
            </div>
            <div className="pricing-card pricing-featured">
              <div className="pricing-badge">推荐</div>
              <h3 className="pricing-name">学期包</h3>
              <div className="pricing-price">{'\u00A559.8'}</div>
              <ul className="pricing-features">
                <li>3 篇综述生成额度</li>
                <li>在线查看 + PDF 导出</li>
                <li>低至 {'\u00A519.9'}/篇</li>
              </ul>
              <button className="pricing-btn pricing-btn-primary" onClick={() => { isLoggedIn ? setShowPaymentModal('semester') : setShowLoginModal(true) }}>选择学期包</button>
            </div>
            <div className="pricing-card">
              <h3 className="pricing-name">学年包</h3>
              <div className="pricing-price">{'\u00A599.8'}</div>
              <ul className="pricing-features">
                <li>6 篇综述生成额度</li>
                <li>在线查看 + PDF 导出</li>
                <li>低至 {'\u00A516.6'}/篇</li>
              </ul>
              <button className="pricing-btn pricing-btn-primary" onClick={() => { isLoggedIn ? setShowPaymentModal('yearly') : setShowLoginModal(true) }}>选择学年包</button>
            </div>
          </div>
        </div>
      </section>

      <footer className="home-footer">
        <div className="footer-content">
          <p className="footer-copyright">© 2026 AutoOverview. All rights reserved.</p>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" className="footer-icp">
            沪ICP备2023018158号-4
          </a>
        </div>
      </footer>

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
          pendingTopic={topic}
        />
      )}

      {showPaymentModal && (
        <PaymentModal
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={() => {
            setShowPaymentModal(false)
            setUserInfo(getLocalUserInfo())
          }}
          planType={showPaymentModal}
        />
      )}
    </div>
  )
}
