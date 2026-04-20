/**
 * Privacy Policy Page - Chinese Version
 * Privacy practices for 澹墨学术 SaaS service
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function PrivacyPolicyPageChinese() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← 返回首页</Link>

        <h1 className="legal-title">隐私政策</h1>
        <p className="legal-effective">最后更新：2026年4月12日</p>

        <section className="legal-section">
          <h2>1. 引言</h2>
          <p>
            澹墨学术（"我们"、"我们的"）尊重您的隐私，并致力于保护您的
            个人数据。本隐私政策解释了当您使用我们的 AI 驱动的文献综述生成服务时，
            我们如何收集、使用、披露和保护您的信息。
          </p>
          <p>
            请仔细阅读本隐私政策。如果您不同意本隐私政策的条款，
            请不要访问服务。
          </p>
        </section>

        <section className="legal-section">
          <h2>2. 我们收集的数据</h2>

          <h3>2.1 个人信息</h3>
          <p>我们收集您直接提供给我们的信息：</p>
          <ul>
            <li><strong>账户信息：</strong>姓名、电子邮件地址和学术机构</li>
            <li><strong>支付信息：</strong>通过支付宝安全处理（我们不存储信用卡详细信息）</li>
            <li><strong>研究主题：</strong>您输入的用于文献综述生成的主题</li>
            <li><strong>生成内容：</strong>通过服务生成的综述和引用</li>
          </ul>

          <h3>2.2 自动收集的信息</h3>
          <p>当您使用服务时，我们会自动收集某些信息：</p>
          <ul>
            <li><strong>使用数据：</strong>查看的页面、使用的功能、花费的时间、访问频率</li>
            <li><strong>设备信息：</strong>浏览器类型、操作系统、IP地址</li>
            <li><strong>日志数据：</strong>访问时间、访问的页面、遇到的错误</li>
          </ul>

          <h3>2.3 Cookie 和跟踪</h3>
          <p>
            我们使用 cookie 和类似技术来改善您的体验、分析使用模式，
            并用于安全目的。您可以通过浏览器设置管理 cookie 首选项。
          </p>
        </section>

        <section className="legal-section">
          <h2>3. 我们如何使用您的数据</h2>
          <p>我们将收集的数据用于以下目的：</p>

          <h3>3.1 服务提供</h3>
          <ul>
            <li>根据您的研究主题处理和生成文献综述</li>
            <li>管理您的账户和积分</li>
            <li>提供客户支持</li>
            <li>发送交易电子邮件（收据、使用通知）</li>
          </ul>

          <h3>3.2 服务改进</h3>
          <ul>
            <li>分析使用模式以提高 AI 模型准确性</li>
            <li>识别和修复技术问题</li>
            <li>开发新功能和服务</li>
          </ul>

          <h3>3.3 安全与欺诈预防</h3>
          <ul>
            <li>检测和防止欺诈活动</li>
            <li>防止未授权访问</li>
            <li>验证用户身份</li>
          </ul>

          <h3>3.4 通信</h3>
          <ul>
            <li>发送产品更新和教育内容（您可以选择退出）</li>
            <li>回复您的查询和支持请求</li>
            <li>通知您重要的服务变更</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>4. 数据共享与披露</h2>

          <h3>4.1 第三方服务提供商</h3>
          <p>我们与帮助我们运营服务的可信赖第三方共享数据：</p>
          <ul>
            <li><strong>支付处理：</strong>支付宝处理支付。我们不存储您的信用卡信息。</li>
            <li><strong>学术数据库：</strong>我们查询公共学术 API（Semantic Scholar、IEEE 等）来检索论文。</li>
            <li><strong>云基础设施：</strong>AWS 和类似提供商托管我们的服务。</li>
            <li><strong>分析：</strong>我们使用分析工具来了解使用模式。</li>
          </ul>

          <h3>4.2 不出售个人数据</h3>
          <p>
            我们不出售、出租或交易您的个人信息。您的研究主题和生成内容
            不会出售给第三方。
          </p>

          <h3>4.3 法律要求</h3>
          <p>
            如果法律要求或响应来自执法部门或其他政府当局的有效法律请求，
            我们可能会披露您的信息。
          </p>

          <h3>4.4 业务转让</h3>
          <p>
            在合并、收购或资产出售的情况下，您的数据可能会转让给
            新所有者。
          </p>
        </section>

        <section className="legal-section">
          <h2>5. 数据保留</h2>

          <h3>5.1 账户数据</h3>
          <p>
            我们在您的账户存续期间以及账户关闭后的合理期限内保留您的账户信息
            和生成的综述，用于法律和运营目的。
          </p>

          <h3>5.2 使用数据</h3>
          <p>
            匿名化的使用数据可能会无限期保留，用于分析和服务改进目的。
          </p>

          <h3>5.3 数据删除</h3>
          <p>
            您可以通过联系我们请求删除您的个人数据。我们将在 30 天内删除您的数据，
            但法律保留要求除外。
          </p>
        </section>

        <section className="legal-section">
          <h2>6. 学术内容与研究主题</h2>

          <h3>6.1 保密性</h3>
          <p>
            您的研究主题和生成的综述安全存储，不能通过您的账户公开访问。
            未经同意，我们不会使用您未发表的研究来训练我们的模型。
          </p>

          <h3>6.2 模型训练</h3>
          <p>
            我们可能会使用匿名化和聚合数据来改进我们的 AI 模型。此数据不包括
            个人身份信息或可以识别您的特定研究内容。
          </p>

          <h3>6.3 公开与私有内容</h3>
          <p>
            只有您可以访问通过您的账户生成的综述。我们网站上显示的演示案例
            要么被明确标记为示例，要么是在用户同意的情况下共享的。
          </p>
        </section>

        <section className="legal-section">
          <h2>7. 数据安全</h2>
          <p>我们实施适当的安全措施来保护您的信息：</p>
          <ul>
            <li><strong>加密：</strong>数据在传输和静态时都被加密</li>
            <li><strong>访问控制：</strong>限制对个人数据的访问</li>
            <li><strong>定期审核：</strong>定期安全评估</li>
            <li><strong>安全支付：</strong>通过支付宝进行符合 PCI 标准的支付处理</li>
          </ul>
          <p>
            尽管我们尽了努力，但没有一种通过互联网传输的方法是 100% 安全的。
            虽然我们努力保护您的数据，但我们不能保证绝对安全。
          </p>
        </section>

        <section className="legal-section">
          <h2>8. 您的权利与选择</h2>
          <p>根据您的位置，您可能拥有以下权利：</p>

          <h3>8.1 账户关闭</h3>
          <p>
            您可以随时通过个人资料设置关闭您的账户。关闭后：
          </p>
          <ul>
            <li>您的账户将立即被标记为非活动状态</li>
            <li>所有对您的综述和积分的访问将被撤销</li>
            <li>您的数据将在 30 天内安排永久删除</li>
            <li>您可以通过联系支持在 30 天内请求重新激活账户</li>
          </ul>

          <h3>8.2 数据删除</h3>
          <p>
            要在 30 天保留期之前请求删除您的个人数据，或者如果您已经
            关闭了账户，请联系我们 scholar@danmo.tech。我们将
            在 30 天内处理您的请求，但法律保留要求除外。
          </p>

          <h3>8.3 数据访问与可移植性</h3>
          <p>
            您可以通过联系我们 scholar@danmo.tech 请求您的个人数据副本。
            我们将在 30 天内以结构化格式提供您的数据。
          </p>

          <h3>8.4 数据更正</h3>
          <p>
            要更新或更正不准确的信息，请联系我们 scholar@danmo.tech，
            提供您希望更改的信息的详细信息。
          </p>

          <h3>8.5 反对与选择退出</h3>
          <p>
            您可以通过联系我们 scholar@danmo.tech 反对某些数据处理活动
            或选择退出营销通信。
          </p>
        </section>

        <section className="legal-section">
          <h2>9. 儿童隐私</h2>
          <p>
            本服务面向至少 13 岁的用户。我们不会故意收集
            13 岁以下儿童的个人信息。如果您是父母或监护人，并且认为您的
            孩子向我们提供了个人数据，请联系我们。
          </p>
        </section>

        <section className="legal-section">
          <h2>10. 本政策的更新</h2>
          <p>
            我们可能会不时更新本隐私政策。我们将通过电子邮件或
            服务通知您重大变更。变更后继续使用即表示接受
            更新后的政策。
          </p>
        </section>

        <section className="legal-section">
          <h2>11. 联系信息</h2>
          <p>
            有关本隐私政策或您的个人数据的问题，请联系我们：
            <br />
            <a href="mailto:scholar@danmo.tech" className="legal-link">
              scholar@danmo.tech
            </a>
          </p>
        </section>

        <footer className="legal-footer">
          <p>© 2026 澹墨学术. 保留所有权利。</p>
        </footer>
      </div>
    </div>
  )
}
