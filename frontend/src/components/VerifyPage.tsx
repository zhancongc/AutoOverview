/**
 * VerifyPage - 文献真实性验证工具
 * 用户粘贴文本或上传 Word/Markdown 文件，系统验证参考文献是否真实
 */
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { isLoggedIn as checkLoggedIn } from '../authApi'
import { LoginModal } from './LoginModal'
import './SimpleApp.css'

interface RefResult {
  raw: string
  title: string
  author: string
  language: string
  verified: boolean
  status: 'verified' | 'not_found' | 'error' | 'skipped'
  match_title?: string
  source?: string
  doi?: string
  url?: string
  message?: string
}

interface VerifyResult {
  total: number
  verified: number
  suspicious: number
  errors: number
  references: RefResult[]
}

export function VerifyPage() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const isEn = i18n.language === 'en'
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [text, setText] = useState('')
  const [fileName, setFileName] = useState('')
  const [fileBytes, setFileBytes] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VerifyResult | null>(null)
  const [error, setError] = useState('')
  const [showLogin, setShowLogin] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      const ext = f.name.split('.').pop()?.toLowerCase()
      if (!['docx', 'md', 'markdown', 'txt'].includes(ext || '')) {
        setError(isEn ? 'Unsupported file format. Please upload .docx or .md files.' : '不支持的文件格式，请上传 .docx 或 .md 文件')
        return
      }
      setFileName(f.name)
      setFileBytes(f)
      setError('')
    }
  }

  const handleVerify = async () => {
    if (!checkLoggedIn()) {
      setShowLogin(true)
      return
    }

    if (!text.trim() && !fileBytes) {
      setError(isEn ? 'Please paste text or upload a file.' : '请粘贴文本或上传文件')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const formData = new FormData()
      if (fileBytes) {
        formData.append('file', fileBytes)
      }
      if (text.trim()) {
        formData.append('text', text)
      }

      const token = localStorage.getItem('auth_token')
      const resp = await axios.post('/api/verify-references', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })

      if (resp.data?.success) {
        setResult(resp.data.data)
      } else {
        setError(resp.data?.detail || (isEn ? 'Verification failed' : '验证失败'))
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setShowLogin(true)
      } else if (err.response?.status === 429) {
        setError(isEn ? 'Too many requests. Please wait a moment.' : '请求过于频繁，请稍后再试')
      } else {
        setError(err.response?.data?.detail || (isEn ? 'Verification failed' : '验证失败'))
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setText('')
    setFileName('')
    setFileBytes(null)
    setResult(null)
    setError('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      {/* Header */}
      <div style={{
        background: '#fff',
        borderBottom: '1px solid #e8e8e8',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
      }}>
        <div
          style={{ cursor: 'pointer', fontWeight: 600, fontSize: '16px', color: '#4F46E5' }}
          onClick={() => navigate('/')}
        >
          Danmo Scholar
        </div>
        <span style={{ color: '#ccc' }}>|</span>
        <span style={{ fontSize: '15px', color: '#333' }}>
          {isEn ? 'Reference Verification' : '文献真实性验证'}
        </span>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Title */}
        <h1 style={{ fontSize: '24px', marginBottom: '8px', color: '#1a1a1a' }}>
          {isEn ? 'Verify Your References' : '验证文献真实性'}
        </h1>
        <p style={{ color: '#666', marginBottom: '24px', fontSize: '14px' }}>
          {isEn
            ? 'Paste your review text or upload a file. We\'ll check if every reference actually exists.'
            : '粘贴综述文本或上传文件，系统将逐条验证每条参考文献是否真实存在。'}
        </p>

        {/* Input Area */}
        <div style={{ marginBottom: '20px' }}>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={
              isEn
                ? 'Paste your text with references here...\n\nExample:\n...\n\nReferences\n[1] Smith, J. et al. "Deep Learning for NLP." Nature, 2023.\n[2] Wang, L. "Attention Mechanism." Science, 2022.'
                : '粘贴含参考文献的文本到这里...\n\n示例：\n...\n\n参考文献\n[1] 张三等. "深度学习在自然语言处理中的应用." 计算机学报, 2023.\n[2] 李四. "注意力机制研究综述." 中国科学, 2022.'
            }
            style={{
              width: '100%',
              minHeight: '220px',
              padding: '14px',
              border: '1px solid #d9d9d9',
              borderRadius: '8px',
              fontSize: '14px',
              lineHeight: '1.6',
              resize: 'vertical',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* File Upload */}
        <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{
            padding: '8px 16px',
            background: '#fff',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            color: '#555',
          }}>
            {isEn ? 'Upload File' : '上传文件'}
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx,.md,.markdown,.txt"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
          </label>
          {fileName && (
            <span style={{ fontSize: '13px', color: '#4F46E5' }}>
              {fileName}
              <span
                style={{ marginLeft: '8px', cursor: 'pointer', color: '#999' }}
                onClick={() => { setFileName(''); setFileBytes(null); if (fileInputRef.current) fileInputRef.current.value = '' }}
              >
                x
              </span>
            </span>
          )}
          <span style={{ fontSize: '12px', color: '#999' }}>
            {isEn ? 'Supports .docx, .md, .txt' : '支持 .docx、.md、.txt'}
          </span>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          <button
            onClick={handleVerify}
            disabled={loading}
            style={{
              padding: '10px 32px',
              background: loading ? '#a5b4fc' : '#4F46E5',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '15px',
              fontWeight: 500,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading
              ? (isEn ? 'Verifying...' : '验证中...')
              : (isEn ? 'Start Verification' : '开始验证')}
          </button>
          {(result || text || fileName) && (
            <button
              onClick={handleReset}
              style={{
                padding: '10px 24px',
                background: '#fff',
                border: '1px solid #d9d9d9',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer',
                color: '#666',
              }}
            >
              {isEn ? 'Reset' : '重置'}
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div style={{ padding: '12px 16px', background: '#fff2f0', border: '1px solid #ffccc7', borderRadius: '8px', marginBottom: '16px', color: '#cf1322', fontSize: '14px' }}>
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div>
            {/* Summary */}
            <div style={{
              display: 'flex',
              gap: '24px',
              marginBottom: '20px',
              padding: '16px 20px',
              background: '#fff',
              borderRadius: '10px',
              border: '1px solid #e8e8e8',
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 600 }}>{result.total}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>{isEn ? 'Total' : '总计'}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 600, color: '#52c41a' }}>{result.verified}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>{isEn ? 'Verified' : '已验证'}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 600, color: result.suspicious > 0 ? '#ff4d4f' : '#999' }}>{result.suspicious}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>{isEn ? 'Suspicious' : '可疑'}</div>
              </div>
              {result.errors > 0 && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 600, color: '#faad14' }}>{result.errors}</div>
                  <div style={{ fontSize: '12px', color: '#888' }}>{isEn ? 'Errors' : '异常'}</div>
                </div>
              )}
            </div>

            {/* Reference List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.references.map((ref, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 16px',
                    background: '#fff',
                    borderRadius: '8px',
                    border: '1px solid',
                    borderColor: ref.verified ? '#b7eb8f' : ref.status === 'error' ? '#ffe58f' : '#ffccc7',
                    borderLeftWidth: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    {/* Status Icon */}
                    <span style={{ fontSize: '16px', flexShrink: 0, marginTop: '2px' }}>
                      {ref.verified ? '✓' : ref.status === 'error' ? '⚠' : '✗'}
                    </span>
                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '13px', color: '#333', lineHeight: '1.5', wordBreak: 'break-word' }}>
                        {ref.raw}
                      </div>
                      {ref.verified && ref.match_title && (
                        <div style={{ marginTop: '6px', fontSize: '12px', color: '#52c41a' }}>
                          {isEn ? 'Matched: ' : '匹配: '}{ref.match_title}
                          {ref.doi && <span style={{ color: '#4F46E5', marginLeft: '8px' }}>DOI: {ref.doi}</span>}
                          {ref.source && <span style={{ color: '#999', marginLeft: '8px' }}>({ref.source})</span>}
                        </div>
                      )}
                      {!ref.verified && ref.status === 'not_found' && (
                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#ff4d4f' }}>
                          {isEn ? 'No matching paper found — this reference may be fabricated.' : '未找到匹配文献 — 该条参考文献可能为虚构。'}
                        </div>
                      )}
                      {ref.status === 'error' && ref.message && (
                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#faad14' }}>
                          {isEn ? 'Verification error: ' : '验证异常: '}{ref.message}
                        </div>
                      )}
                      {ref.status === 'skipped' && (
                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#999' }}>
                          {isEn ? 'Could not extract title.' : '无法提取标题。'}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Login Modal */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onLoginSuccess={() => { setShowLogin(false); handleVerify(); }}
        />
      )}
    </div>
  )
}
