/**
 * 综述展示组件
 */
import ReactMarkdown from 'react-markdown'

interface ReviewPanelProps {
  review: string
  statistics: any
}

export function ReviewPanel({ review, statistics }: ReviewPanelProps) {
  if (!review) {
    return (
      <div className="review-placeholder">
        <p>请先生成综述</p>
      </div>
    )
  }

  return (
    <div className="review-panel">
      <div className="review-header">
        <h3>📝 文献综述</h3>
        {statistics && (
          <div className="review-stats">
            <span>文献: {statistics.total || 0} 篇</span>
            <span>引用: {statistics.total_citations || 0} 次</span>
            <span>平均被引: {statistics.avg_citations?.toFixed(1) || 0}</span>
          </div>
        )}
      </div>

      <div className="review-content">
        <ReactMarkdown>{review}</ReactMarkdown>
      </div>
    </div>
  )
}
