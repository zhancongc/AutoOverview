/**
 * 智能分析面板组件
 */
import { TopicClassification } from '../types'

interface AnalysisPanelProps {
  classification: TopicClassification | null
  frameworkType: string
}

export function AnalysisPanel({ classification, frameworkType }: AnalysisPanelProps) {
  if (!classification) {
    return (
      <div className="analysis-placeholder">
        <p>请先进行智能分析</p>
      </div>
    )
  }

  const { type, type_name, classification_reason, key_elements } = classification

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h3>📊 题目类型分析</h3>
        <div className="type-badge">
          <span className="type-label">类型：</span>
          <span className="type-value">{type_name}</span>
        </div>
      </div>

      <div className="analysis-content">
        <div className="analysis-reason">
          <h4>判定依据：</h4>
          <p>{classification_reason}</p>
        </div>

        {key_elements && Object.keys(key_elements).length > 0 && (
          <div className="key-elements">
            <h4>关键要素：</h4>
            <ul>
              {key_elements.variables && (
                <>
                  <li>自变量：{key_elements.variables.independent}</li>
                  <li>因变量：{key_elements.variables.dependent}</li>
                </>
              )}
              {key_elements.research_object && (
                <li>研究对象：{key_elements.research_object}</li>
              )}
              {key_elements.optimization_goal && (
                <li>优化目标：{key_elements.optimization_goal}</li>
              )}
              {key_elements.methodology && (
                <li>方法论：{key_elements.methodology}</li>
              )}
            </ul>
          </div>
        )}

        <div className="framework-info">
          <h4>综述框架：</h4>
          <p>{frameworkType === 'three-circles' ? '三圈交集式（研究对象+优化目标+方法论）' :
               frameworkType === 'pyramid' ? '金字塔式（理论基础→指标体系→方法技术→实践应用）' :
               frameworkType === 'problem-solution' ? '问题-方案式（研究问题→理论基础→影响机制）' :
               '通用结构'}
          </p>
        </div>
      </div>
    </div>
  )
}
