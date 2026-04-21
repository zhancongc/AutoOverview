import { Link } from 'react-router-dom'
import './LegalPages.css'

export function AcademicIntegrityPageChinese() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← 返回首页</Link>

        <h1 className="legal-title">学术诚信声明</h1>
        <p className="legal-effective">最后更新：2026年4月19日</p>

        <section className="legal-section">
          <h2>我们对学术诚信的承诺</h2>
          <p>
            澹墨学术是一款<strong>文献发现与整理工具</strong>，旨在帮助研究人员、研究生和学者高效地查找、比较和整理论文。
            我们致力于支持符合道德规范的学术行为，倡导负责任地使用 AI 辅助研究工具。
          </p>
          <p>
            我们的平台类似于 Elicit、Connected Papers、Consensus 等成熟的学术工具——
            都是帮助研究人员在浩瀚的学术文献中进行导航和探索的辅助工具。
          </p>
        </section>

        <section className="legal-section">
          <h2>澹墨学术的功能</h2>
          <ul>
            <li><strong>文献搜索与发现</strong> — 通过 OpenAlex（全球最大的开放学术数据库之一）检索海量学术论文</li>
            <li><strong>论文对比</strong> — 多篇论文的研究方法、核心发现和关键指标并排对比</li>
            <li><strong>引用整理</strong> — 支持多种引用格式（IEEE、APA、MLA、GB/T 7714），可导出 BibTeX、RIS 或 Word 格式</li>
            <li><strong>来源验证</strong> — 每篇论文结果均包含 Google Scholar 和 DOI 直链，方便对照原始文献</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>澹墨学术不会做的事</h2>
          <ul>
            <li>我们<strong>不会</strong>代替用户撰写论文、报告或任何学术内容</li>
            <li>我们<strong>不会</strong>充当论文代写、代发或润色机构</li>
            <li>我们<strong>不会</strong>鼓励或协助任何形式的抄袭行为</li>
            <li>我们<strong>不会</strong>绕过学术写作规范和要求</li>
            <li>我们<strong>不会</strong>取代批判性思维、原创分析或学术判断</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>预期使用方式</h2>
          <p>
            用户应将澹墨学术作为<strong>研究辅助工具</strong>使用——类似于搜索引擎、文献管理软件或学术数据库。
            我们提供的文献整理和摘要内容仅是研究的起点，而非最终的学术成果。
          </p>
          <p>
            我们强烈建议所有用户：
          </p>
          <ul>
            <li>阅读并批判性评估结果中引用的所有原始论文</li>
            <li>通过提供的 Google Scholar 和 DOI 链接对照一手来源验证信息</li>
            <li>在撰写文献综述时加入自己的分析、综合和批判性观点</li>
            <li>遵守所在机构的学术诚信和引用规范</li>
            <li>按照适用的引用标准正确引用所有来源</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>禁止用途</h2>
          <p>
            以下行为严格禁止：
          </p>
          <ul>
            <li>将 AI 生成或整理的内容作为自己的原创学术成果提交，且未进行适当的标注和实质性修改</li>
            <li>使用本工具为他人代写作业、论文或学位论文</li>
            <li>任何形式的学术不端行为，包括但不限于抄袭、捏造数据或学术欺诈</li>
            <li>将生成的内容转售或再分发作为学术写作服务</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>违规处理</h2>
          <p>
            我们保留暂停或终止违反本学术诚信声明的账户的权利。
            如果我们发现本工具被用于学术不端行为，我们将采取适当措施，包括但不限于账户暂停，
            以及在法律要求时向相关机构报告。
          </p>
        </section>

        <section className="legal-section">
          <h2>联系我们</h2>
          <p>
            如果您对本声明有任何疑问，或希望举报潜在的滥用行为，请通过{' '}
            <a href="mailto:service@danmo.tech">service@danmo.tech</a> 联系我们。
          </p>
        </section>
      </div>
    </div>
  )
}
