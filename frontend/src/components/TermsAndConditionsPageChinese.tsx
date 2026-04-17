/**
 * Terms & Conditions Page - Chinese Version
 * Legal terms for 澹墨学术 SaaS service
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function TermsAndConditionsPageChinese() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← 返回首页</Link>

        <h1 className="legal-title">用户协议</h1>
        <p className="legal-effective">最后更新：2026年4月12日</p>

        <section className="legal-section">
          <h2>1. 协议接受</h2>
          <p>
            访问或使用 澹墨学术（"服务"）即表示您同意受本用户协议的约束。
            如果您不同意这些条款，请不要使用我们的服务。
          </p>
        </section>

        <section className="legal-section">
          <h2>2. 服务描述</h2>
          <p>
            澹墨学术 是一个 AI 驱动的文献综述生成服务，专为学术和研究目的而设计。
            该服务根据用户提供的研究主题，自动搜索学术数据库并生成全面的文献综述。
          </p>
          <p><strong>主要功能：</strong></p>
          <ul>
            <li>从学术数据库自动搜索论文</li>
            <li>AI 生成带有正确引用的文献综述</li>
            <li>多种格式的导出功能</li>
            <li>基于积分的使用系统</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>3. 用户责任</h2>
          <p>作为服务用户，您同意：</p>
          <ul>
            <li>注册时提供准确完整的信息</li>
            <li>仅将服务用于合法的学术目的</li>
            <li>不试图规避使用限制或积分限制</li>
            <li>不与他人共享您的账户凭证</li>
            <li>在提交或发表前验证生成的内容</li>
            <li>根据学术标准正确引用 AI 生成的内容</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>4. 知识产权</h2>
          <p><strong>4.1 服务所有权</strong></p>
          <p>
            澹墨学术 平台、技术和所有内容（不包括用户提交的主题）均归
            澹墨学术 所有，并受知识产权法保护。
          </p>

          <p><strong>4.2 生成内容</strong></p>
          <p>
            您保留通过服务生成的文献综述的所有权。但是，您确认
            此类内容是 AI 生成的，应进行验证并正确署名。
          </p>

          <p><strong>4.3 学术诚信</strong></p>
          <p>
            用户有责任确保遵守其机构的学术诚信政策。
            AI 生成的内容应作为研究辅助工具，而不是原创作品的替代品。
          </p>
        </section>

        <section className="legal-section">
          <h2>5. 支付与积分</h2>
          <p><strong>5.1 基于积分的系统</strong></p>
          <p>
            本服务采用基于积分的系统。每生成一篇文献综述消耗一个积分。
            积分可以通过各种套餐购买（单次、学期、学年）。
          </p>

          <p><strong>5.2 支付条款</strong></p>
          <ul>
            <li>支付通过支付宝安全处理（中国用户）</li>
            <li>所有价格以人民币显示</li>
            <li>已使用的积分不予退款</li>
            <li>未使用的积分根据所购买套餐条款过期</li>
          </ul>

          <p><strong>5.3 服务可用性</strong></p>
          <p>
            虽然我们努力实现 99.9% 的正常运行时间，但我们不保证服务的不间断访问。
            计划内维护可能会在可能的情况下提前通知。
          </p>
        </section>

        <section className="legal-section">
          <h2>6. 责任限制</h2>
          <p><strong>6.1 服务准确性</strong></p>
          <p>
            本服务使用 AI 和自动化系统搜索和综合信息。虽然我们努力
            确保准确性，但我们不能保证所有生成的内容都是无错误的。
            用户在依赖信息用于学术或专业目的之前必须验证所有信息。
          </p>

          <p><strong>6.2 损害赔偿</strong></p>
          <p>
            在任何情况下，澹墨学术 均不对任何间接、附带、特殊、后果性或
            惩罚性损害承担责任，包括但不限于利润、数据、使用、商誉或其他
            无形损失的损失。
          </p>

          <p><strong>6.3 最高责任</strong></p>
          <p>
            我们的总责任不得超过您在索赔前十二（12）个月内
            为服务支付的金额。
          </p>
        </section>

        <section className="legal-section">
          <h2>7. 禁止使用</h2>
          <p>您不得使用本服务：</p>
          <ul>
            <li>为欺诈或欺骗目的生成内容</li>
            <li>违反任何适用法律或法规</li>
            <li>侵犯他人的知识产权</li>
            <li>试图获得对我们系统的未授权访问</li>
            <li>未经适当许可将服务用于商业目的</li>
            <li>在没有署名的情况下将 AI 生成的作品完全作为您自己的作品</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>8. 账户暂停与终止</h2>
          <p><strong>8.1 暂停</strong></p>
          <p>
            如果您违反这些条款或从事欺诈活动，我们保留暂停或终止您账户的权利。
          </p>

          <p><strong>8.2 退款</strong></p>
          <p>
            除适用法律要求外，暂停或终止的账户无权获得未使用积分的退款。
            有关详情，请参阅我们的退款政策。
          </p>
        </section>

        <section className="legal-section">
          <h2>9. 服务修改</h2>
          <p>
            我们保留随时修改、暂停或终止服务（或其任何部分）的权利，
            无论是否通知。我们不对您或任何第三方因服务的修改、
            暂停或终止承担责任。
          </p>
        </section>

        <section className="legal-section">
          <h2>10. 隐私与数据</h2>
          <p>
            您的隐私对我们很重要。请查看我们的隐私政策，了解我们如何收集、使用和
            保护您的信息。
          </p>
        </section>

        <section className="legal-section">
          <h2>11. 适用法律</h2>
          <p>
            这些条款受中华人民共和国法律管辖和解释，
            不考虑其法律冲突规定。
          </p>
        </section>

        <section className="legal-section">
          <h2>12. 条款变更</h2>
          <p>
            我们可能会不时更新这些用户协议。我们将通过电子邮件或
            服务通知用户重大变更。变更后继续使用即表示接受新条款。
          </p>
        </section>

        <section className="legal-section">
          <h2>13. 联系信息</h2>
          <p>
            有关这些用户协议的问题，请联系我们：
            <br />
            <a href="mailto:support@snappicker.com" className="legal-link">
              support@snappicker.com
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
