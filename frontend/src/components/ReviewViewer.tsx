import { useState, useEffect, useMemo, useRef, useCallback, Fragment } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CitationTooltip, CitationMarker, CitationRangeMarker } from './CitationTooltip'
import { useTranslation } from 'react-i18next'
import './ReviewViewer.css'

interface TableOfContents {
  id: string
  text: string
  level: number
  children: TableOfContents[]
}

interface ReviewViewerProps {
  title: string
  content: string
  papers?: Array<{
    id: string
    title: string
    authors: string[]
    year: number
    doi?: string
    url?: string
  }>
  hasPurchased?: boolean
  onTocUpdate?: (toc: TableOfContents[]) => void
  onRequestUnlock?: () => void
}

export function ReviewViewer({ content, papers = [], hasPurchased = false, onTocUpdate, onRequestUnlock }: ReviewViewerProps) {
  const { t } = useTranslation()
  const [toc, setToc] = useState<TableOfContents[]>([])
  const [activeId, setActiveId] = useState<string>('')
  const [showReferencesPopup, setShowReferencesPopup] = useState(false)
  useRef<HTMLElement>(null)
  const isClickScrolling = useRef(false)
  const popupRef = useRef<HTMLDivElement>(null)

  // 渲染带引用标记的文本
  const renderTextWithCitations = useCallback((text: any): any => {
    // 处理 null/undefined
    if (text === null || text === undefined) {
      return text
    }

    // 如果是数组，递归处理每个元素
    if (Array.isArray(text)) {
      return text.map((item, i) => (
        <Fragment key={i}>{renderTextWithCitations(item)}</Fragment>
      ))
    }

    // 如果是对象（React 元素），递归处理其 children
    if (typeof text === 'object' && text !== null) {
      // 如果已经是 React 元素，直接返回（避免重复处理）
      // 简单检查：是否有 $$typeof 和 type 属性
      if (text.$$typeof && text.type) {
        return text
      }
      return text
    }

    // 处理字符串
    if (typeof text !== 'string') {
      return text
    }

    // 清理：去掉引用标记前面不必要的逗号和空格（如 ", [1]" -> "[1]"）
    let cleanedText = text.replace(/,\s*(?=\[\d+\])/g, ' ')

    // 清理嵌套的方括号格式：[[11],[14]] -> [11][14] -> 后续会合并为 [11, 14]
    // 匹配 [[开头，]] 结尾，中间是 [数字],[数字]... 格式
    cleanedText = cleanedText.replace(/\[\[([\d,\[\]\s]+)\]\]/g, (_, content) => {
      // content 如 "[11],[14]" 或 "[11],[14],[15]"
      // 去掉外层方括号后变成 [11],[14]，后续步骤会处理
      return content
    })

    // 检测并排序连续的引用标记
    // 匹配连续的 [数字] 引用，如 [5][8][4]
    const consecutiveCitationsPattern = /(\[\d+\]\s*){2,}/g
    cleanedText = cleanedText.replace(consecutiveCitationsPattern, (match) => {
      // 提取所有引用数字
      const citations = match.match(/\[(\d+)\]/g)
      if (citations) {
        const numbers = citations.map(c => parseInt(c.replace(/[\[\]]/g, '')))
        // 排序去重
        numbers.sort((a, b) => a - b)
        const unique = [...new Set(numbers)]
        // 将连续数字合并为范围：[7, 8, 9, 11, 12] → "7-9, 11, 12"
        const ranges: string[] = []
        let rangeStart = unique[0]
        let rangeEnd = unique[0]
        for (let i = 1; i < unique.length; i++) {
          if (unique[i] === rangeEnd + 1) {
            rangeEnd = unique[i]
          } else {
            ranges.push(rangeStart === rangeEnd ? `${rangeStart}` : `${rangeStart}-${rangeEnd}`)
            rangeStart = unique[i]
            rangeEnd = unique[i]
          }
        }
        ranges.push(rangeStart === rangeEnd ? `${rangeStart}` : `${rangeStart}-${rangeEnd}`)
        return `[${ranges.join(', ')}]`
      }
      return match
    })

    // 匹配 [数字] 或 [数字, 数字, ...] 或 [数字-数字] 等格式的引用
    // 使用捕获组保留分隔符
    const parts = cleanedText.split(/(\[\d[\d,\s\-]*\d\]|\[\d+\])/g)

    // 展开引用范围：[7-9, 11] → [7, 8, 9, 11]
    const expandRange = (str: string): number[] => {
      const nums: number[] = []
      str.split(',').forEach(seg => {
        const trimmed = seg.trim()
        const rangeMatch = trimmed.match(/^(\d+)\s*-\s*(\d+)$/)
        if (rangeMatch) {
          const start = parseInt(rangeMatch[1])
          const end = parseInt(rangeMatch[2])
          for (let i = start; i <= end; i++) nums.push(i)
        } else {
          const n = parseInt(trimmed)
          if (!isNaN(n)) nums.push(n)
        }
      })
      return nums
    }

    return parts.map((part, index) => {
      // 跳过空字符串
      if (part === '' || part === ' ') {
        return null
      }

      // 检查是否是引用标记
      const match = part.match(/\[(.+)\]/)
      if (match) {
        const indices = expandRange(match[1])
        // 如果是单个引用
        if (indices.length === 1) {
          const citationIndex = indices[0] - 1
          const paper = papers[citationIndex]
          return <CitationMarker key={`${index}-${indices[0]}`} index={indices[0]} paper={paper} />
        }
        // 多引用：渲染一个可点击的 span，弹窗显示所有文献
        const citedPapers = indices.map(idx => ({ index: idx, paper: papers[idx - 1] }))
        return (
          <CitationRangeMarker key={`range-${index}`} display={part} citations={citedPapers} />
        )
      }
      return part
    }).filter(Boolean)
  }, [papers])

  // 生成标题 ID（与 Markdown 渲染器保持一致）
  const headingIdMap = useRef<Map<string, string>>(new Map())

  // 统一的 id 生成函数
  const makeId = (text: string) => text.toLowerCase().replace(/[^\w\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '')

  // 统一的文本清洗：去掉 Markdown 格式标记
  const stripMd = (text: string) => text.replace(/\*\*/g, '').replace(/\*/g, '').replace(/__/g, '').replace(/_/g, '').trim()

  // 从 React children 中递归提取纯文本
  const extractText = (children: any): string => {
    if (typeof children === 'string') return stripMd(children)
    if (typeof children === 'number') return String(children)
    if (Array.isArray(children)) return children.map(extractText).join('')
    if (children?.props?.children) return extractText(children.props.children)
    return ''
  }

  // 存储参考文献标题的信息
  const [referencesInfo, setReferencesInfo] = useState<{ level: number, number: number } | null>(null)

  // 预处理 content：把没有 # 前缀但以 **数字.数字** 开头的粗体行转为 #### 标题
  // 同时去掉正文中的 "## References" 部分（我们会手动添加带正确序号的版本）
  const processedContent = useMemo(() => {
    let lines = content.split('\n')

    // 查找 "## References" 或类似标题的位置
    let referencesIndex = -1
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (line.match(/^#{1,2}\s*(References|参考文献)/i)) {
        referencesIndex = i
        break
      }
    }

    // 如果找到了 References 标题，去掉它及之后的所有内容
    if (referencesIndex >= 0) {
      lines = lines.slice(0, referencesIndex)
    }

    // 处理标题格式
    return lines.map(line => {
      if (line.match(/^\*\*\d+\.\d+/) && !line.startsWith('#')) {
        return '#### ' + line
      }
      return line
    }).join('\n')
  }, [content])

  // 解析 Markdown 生成目录
  useEffect(() => {
    const lines = processedContent.split('\n')
    const headings: Array<{ id: string; text: string; level: number; originalLevel: number }> = []
    const idCount: Record<string, number> = {}

    lines.forEach((line) => {
      const match = line.match(/^(#{1,4})\s+(.+)$/)
      if (match) {
        const originalLevel = match[1].length
        const rawText = stripMd(match[2])
        const baseId = makeId(rawText)
        idCount[baseId] = (idCount[baseId] || 0) + 1
        const id = idCount[baseId] > 1 ? `${baseId}-${idCount[baseId]}` : baseId

        headings.push({ id, text: rawText, level: originalLevel, originalLevel })
        headingIdMap.current.set(rawText, id)
      }
    })

    // 找到正文一级标题的信息
    let refLevel = 2 // 默认用 h2
    let refNumber = 1
    let minOriginalLevel = 2

    if (headings.length > 0) {
      minOriginalLevel = Math.min(...headings.map(h => h.originalLevel))

      // 找到最后一个以数字开头的标题（如"7. 结论"）
      for (let i = headings.length - 1; i >= 0; i--) {
        const numMatch = headings[i].text.match(/^(\d+)\./)
        if (numMatch) {
          refNumber = parseInt(numMatch[1]) + 1
          // 这个标题的原始级别就是我们要给参考文献用的级别
          refLevel = headings[i].originalLevel
          break
        }
      }
    }

    setReferencesInfo({ level: refLevel, number: refNumber })

    // 标准化标题级别：让最高级标题从 level 1 开始
    let normalizedHeadings = [...headings]
    if (normalizedHeadings.length > 0) {
      normalizedHeadings = normalizedHeadings.map(h => ({ ...h, level: h.originalLevel - minOriginalLevel + 1 }))
    }

    // 构建嵌套的目录结构
    const buildTocTree = (items: Array<{ id: string; text: string; level: number }>): TableOfContents[] => {
      const result: TableOfContents[] = []
      const stack: Array<{ node: TableOfContents; level: number }> = []

      items.forEach(item => {
        const node: TableOfContents = {
          id: item.id,
          text: item.text,
          level: item.level,
          children: []
        }

        while (stack.length > 0 && stack[stack.length - 1].level >= item.level) {
          stack.pop()
        }

        if (stack.length === 0) {
          result.push(node)
        } else {
          stack[stack.length - 1].node.children.push(node)
        }

        stack.push({ node, level: item.level })
      })

      // 添加"参考文献"到目录（带序号）
      if (papers.length > 0) {
        // 计算参考文献在目录中的 level（标准化后的）
        const tocRefLevel = refLevel - minOriginalLevel + 1
        result.push({
          id: 'references-section-title',
          text: `${refNumber}. 参考文献`,
          level: tocRefLevel,
          children: []
        })
      }

      return result
    }

    setToc(buildTocTree(normalizedHeadings))
  }, [processedContent, papers.length])

  // 通知父组件 TOC 更新
  useEffect(() => {
    if (onTocUpdate && toc.length > 0) {
      onTocUpdate(toc)
    }
  }, [toc, onTocUpdate])

  // 点击外部关闭参考文献弹窗
  useEffect(() => {
    if (!showReferencesPopup) return

    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        setShowReferencesPopup(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showReferencesPopup])

  // 监听滚动，高亮当前章节
  useEffect(() => {
    const handleScroll = () => {
      if (isClickScrolling.current) return

      const headings = document.querySelectorAll('.review-body h1[id], .review-body h2[id], .review-body h3[id], .review-body h4[id]')
      const scrollPosition = window.scrollY + 100

      let currentId = ''
      headings.forEach(heading => {
        const element = heading as HTMLElement
        if (element.offsetTop <= scrollPosition) {
          currentId = element.id
        }
      })

      if (currentId !== activeId) {
        setActiveId(currentId)
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [activeId])

  // 点击目录项滚动到对应标题
  const handleTocClick = useCallback((id: string) => (e: any) => {
    e.preventDefault()
    const element = document.getElementById(id) as HTMLElement
    if (!element) return

    isClickScrolling.current = true
    setActiveId(id)

    element.scrollIntoView({ behavior: 'smooth', block: 'start' })

    window.scrollTo({ top: element.offsetTop - 80, behavior: 'smooth' })

    setTimeout(() => {
      isClickScrolling.current = false
    }, 800)
  }, [])

  // 渲染目录项
  const renderTocItem = (item: TableOfContents) => (
    <li key={item.id} className={`toc-item toc-level-${item.level} ${activeId === item.id ? 'active' : ''}`}>
      <a
        href={`#${item.id}`}
        onClick={handleTocClick(item.id)}
      >
        {item.text}
      </a>
      {item.children.length > 0 && (
        <ul className="toc-children">
          {item.children.map(renderTocItem)}
        </ul>
      )}
    </li>
  )

  // 自定义 Markdown 渲染器，添加 id 到标题（与目录 ID 保持一致）
  const components = useMemo(() => ({
    h1: ({ children, ...props }: any) => {
      const text = extractText(children)
      const id = headingIdMap.current.get(text) || makeId(text)
      return <h1 id={id} {...props}>{children}</h1>
    },
    h2: ({ children, ...props }: any) => {
      const text = extractText(children)
      const id = headingIdMap.current.get(text) || makeId(text)
      return <h2 id={id} {...props}>{children}</h2>
    },
    h3: ({ children, ...props }: any) => {
      const text = extractText(children)
      const id = headingIdMap.current.get(text) || makeId(text)
      return <h3 id={id} {...props}>{children}</h3>
    },
    h4: ({ children, ...props }: any) => {
      const text = extractText(children)
      const id = headingIdMap.current.get(text) || makeId(text)
      return <h4 id={id} {...props}>{children}</h4>
    },
    // 自定义段落渲染，处理引用标记
    p: ({ children, ...props }: any) => {
      return (
        <p {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </p>
      )
    },
    // 列表项也处理引用标记
    li: ({ children, ...props }: any) => {
      return (
        <li {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </li>
      )
    },
    // 表格单元格也处理引用标记
    td: ({ children, ...props }: any) => {
      return (
        <td {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </td>
      )
    },
    // 表格标题单元格也处理引用标记
    th: ({ children, ...props }: any) => {
      return (
        <th {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </th>
      )
    },
    // 粗体文本也处理引用标记
    strong: ({ children, ...props }: any) => {
      return (
        <strong {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </strong>
      )
    },
    // 斜体文本也处理引用标记
    em: ({ children, ...props }: any) => {
      return (
        <em {...props}>
          {Array.isArray(children)
            ? children.map((child, i) => <Fragment key={i}>{renderTextWithCitations(child)}</Fragment>)
            : renderTextWithCitations(children)
          }
        </em>
      )
    }
  }), [headingIdMap, makeId, renderTextWithCitations])

  // 单条参考文献带弹窗的组件
  const ReferenceListItem = ({ paper, index }: { paper: any; index: number }) => {
    const [showTooltip, setShowTooltip] = useState(false)
    const [isFixed, setIsFixed] = useState(false)
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
    const hoverTimerRef = useRef<NodeJS.Timeout | null>(null)

    const getPosition = (el: HTMLElement) => {
      const rect = el.getBoundingClientRect()
      const isMobile = window.innerWidth < 768
      if (isMobile) {
        return { x: 16, y: rect.bottom + 8 }
      }
      return { x: rect.right, y: rect.top }
    }

    const handleMouseEnter = (e: React.MouseEvent) => {
      if (isFixed) return
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
      hoverTimerRef.current = setTimeout(() => {
        setTooltipPos(getPosition(e.currentTarget as HTMLElement))
        setShowTooltip(true)
      }, 200)
    }

    const handleMouseLeave = () => {
      if (isFixed) return
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
      setShowTooltip(false)
    }

    const handleClick = (e: React.MouseEvent) => {
      e.preventDefault()
      setTooltipPos(getPosition(e.currentTarget as HTMLElement))
      if (isFixed) {
        setIsFixed(false)
        setShowTooltip(false)
      } else {
        setIsFixed(true)
        setShowTooltip(true)
      }
    }

    const handleClose = () => {
      setIsFixed(false)
      setShowTooltip(false)
    }

    return (
      <li style={{ marginBottom: '0.75rem', lineHeight: 1.6, color: '#2D3436' }}>
        <span
          className="reference-item-clickable"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          style={{ cursor: 'pointer', display: 'inline' }}
        >
          {paper.authors.join(', ')}. ({paper.year}). {paper.title}.
        </span>
        {showTooltip && (
          <CitationTooltip
            index={index + 1}
            paper={paper}
            targetPosition={tooltipPos}
            isFixed={isFixed}
            onClose={handleClose}
          />
        )}
      </li>
    )
  }

  // 生成第三方平台验证链接
  const getVerificationLinks = (paper: any) => {
    const links = []

    // 构建搜索查询
    const searchQuery = encodeURIComponent(paper.title)

    // Google Scholar
    links.push({
      name: 'Google Scholar',
      url: `https://scholar.google.com/scholar?q=${searchQuery}`,
      icon: '🔬',
      color: '#4285f4'
    })

    // 百度学术
    links.push({
      name: '百度学术',
      url: `https://xueshu.baidu.com/s?wd=${searchQuery}`,
      icon: '🎓',
      color: '#2932e1'
    })

    // DOI
    if (paper.doi) {
      links.push({
        name: 'DOI',
        url: `https://doi.org/${paper.doi}`,
        icon: '🔗',
        color: '#7f8c8d'
      })
    }

    return links
  }

  return (
    <div className={`review-viewer ${!hasPurchased ? 'review-protected' : ''}`}>
      <div className="review-content-wrapper">
        {/* 侧边栏目录 */}
        <aside className="review-sidebar">
          <div className="toc-header">目录</div>
          <ul className="toc-list">
            {toc.map(renderTocItem)}
          </ul>
        </aside>

        {/* 正文内容 */}
        <main className="review-main"
          onContextMenu={(e) => !hasPurchased && e.preventDefault()}
          onCopy={(e) => !hasPurchased && e.preventDefault()}
          onCut={(e) => !hasPurchased && e.preventDefault()}
        >
          {!hasPurchased && (
            <div className="review-watermark" onClick={onRequestUnlock} style={onRequestUnlock ? { cursor: 'pointer' } : undefined}>
              <span className="watermark-text">澹墨学术 预览版</span>
              <span className="watermark-subtext">购买后解锁无水印 Word 导出</span>
            </div>
          )}
          <div className="review-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
              {processedContent}
            </ReactMarkdown>

            {/* 参考文献列表 - 标准格式 */}
            {papers.length > 0 && referencesInfo && (
              <>
                {referencesInfo.level === 1 && <h1 id="references-section-title" onClick={() => setShowReferencesPopup(true)} style={{ cursor: 'pointer' }}>{referencesInfo.number}. 参考文献</h1>}
                {referencesInfo.level === 2 && <h2 id="references-section-title" onClick={() => setShowReferencesPopup(true)} style={{ cursor: 'pointer' }}>{referencesInfo.number}. 参考文献</h2>}
                {referencesInfo.level === 3 && <h3 id="references-section-title" onClick={() => setShowReferencesPopup(true)} style={{ cursor: 'pointer' }}>{referencesInfo.number}. 参考文献</h3>}
                {referencesInfo.level === 4 && <h4 id="references-section-title" onClick={() => setShowReferencesPopup(true)} style={{ cursor: 'pointer' }}>{referencesInfo.number}. 参考文献</h4>}
                <ol style={{ listStyle: 'decimal', paddingLeft: '1.75rem', margin: 0 }}>
                  {papers.map((paper: any, index: number) => (
                    <ReferenceListItem key={paper.id} paper={paper} index={index} />
                  ))}
                </ol>
              </>
            )}

            {/* 参考文献弹窗 */}
            {showReferencesPopup && (
              <div className="references-popup-overlay" onClick={() => setShowReferencesPopup(false)}>
                <div ref={popupRef} className="references-popup" onClick={(e) => e.stopPropagation()}>
                  <div className="references-popup-header">
                    <span className="references-popup-title">{t('review.references.title', '参考文献')} ({papers.length})</span>
                    <button className="references-popup-close" onClick={() => setShowReferencesPopup(false)}>✕</button>
                  </div>
                  <div className="references-popup-list">
                    {papers.map((paper: any, index) => {
                      const verificationLinks = getVerificationLinks(paper)
                      return (
                        <div key={paper.id} className="references-popup-item">
                          <span className="references-popup-index">[{index + 1}]</span>
                          <div className="references-popup-content">
                            <div className="references-popup-paper-title">
                              {verificationLinks[0]?.url ? (
                                <a href={verificationLinks[0].url} target="_blank" rel="noopener noreferrer">
                                  {paper.title}
                                </a>
                              ) : (
                                paper.title
                              )}
                            </div>
                            <div className="references-popup-paper-meta">
                              <span>{paper.authors.join(', ')}</span>
                              <span> ({paper.year})</span>
                            </div>
                            <div className="references-popup-links">
                              {verificationLinks.map((link: any) => (
                                <a
                                  key={link.name}
                                  href={link.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="references-popup-link"
                                  style={{ '--link-color': link.color } as any}
                                >
                                  <span className="references-popup-link-icon">{link.icon}</span>
                                  <span>{link.name}</span>
                                </a>
                              ))}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
