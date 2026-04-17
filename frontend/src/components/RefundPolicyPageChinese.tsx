/**
 * Refund Policy Page - Chinese Version
 * Refund terms for AutoOverview SaaS service
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function RefundPolicyPageChinese() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← 返回首页</Link>

        <h1 className="legal-title">退款政策</h1>
        <p className="legal-effective">最后更新：2026年4月12日</p>

        <section className="legal-section">
          <h2>1. 概述</h2>
          <p>
            在 AutoOverview，我们努力提供高质量的 AI 驱动文献综述服务。
            本退款政策概述了可以退款的情况。
            请在购买前仔细阅读本政策。
          </p>
          <p className="policy-highlight">
            <strong>重要提示：</strong>AutoOverview 是一种低频、必要的学术 SaaS 服务。
            由于 AI 生成内容和即时服务交付的性质，退款处理方式
            与传统产品不同。
          </p>
        </section>

        <section className="legal-section">
          <h2>2. 不可退款的购买</h2>

          <h3>2.1 已使用的积分</h3>
          <p>
            <strong>所有已使用的积分均不可退款。</strong>一旦使用积分生成了文献综述，
            该积分将无法退款。这是因为：
          </p>
          <ul>
            <li>AI 处理成本在生成时立即产生</li>
            <li>学术数据库查询是实时执行的</li>
            <li>服务在完成时立即交付价值</li>
          </ul>

          <h3>2.2 数字内容交付</h3>
          <p>
            一旦文献综述生成并交付到您的账户，交易即
            视为完成。由于数字内容的性质和知识产权考虑，
            我们无法为已完成的综述提供退款。
          </p>

          <h3>2.3 套餐积分</h3>
          <p>
            购买的积分套餐（单次、学期、学年）一旦使用了该套餐中的任何积分，
            即不可退款。套餐中未使用的积分不能退款，
            但可以在到期日前使用。
          </p>
        </section>

        <section className="legal-section">
          <h2>3. 退款资格</h2>

          <h3>3.1 技术故障</h3>
          <p>
            在以下情况下，您可能有资格获得退款或积分替换：
          </p>
          <ul>
            <li>由于我们这边的技术问题，服务未能生成综述</li>
            <li>综述已生成但包含严重的格式错误，导致无法导出</li>
            <li>服务在您的付费访问期间长时间不可用</li>
          </ul>
          <p>
            在这些情况下，我们将调查问题，并可能根据我们的判断
            提供积分替换或部分退款。
          </p>

          <h3>3.2 意外购买</h3>
          <p>
            如果您意外购买了套餐且未使用该套餐中的任何积分，请在购买后
            <strong>7 天内</strong>联系我们。如果符合以下条件，我们可能会全额退款：
          </p>
          <ul>
            <li>套餐中的积分尚未使用</li>
            <li>请求在购买后 7 天内提出</li>
            <li>您可以证明购买的意外性质</li>
          </ul>

          <h3>3.3 重复收费</h3>
          <p>
            如果您因同一购买被意外多次收费，我们将退还重复
            收费。请提供您的交易详情联系我们。
          </p>
        </section>

        <section className="legal-section">
          <h2>4. 不符合条件的情况</h2>

          <h3>4.1 对结果不满意</h3>
          <p>
            以下情况不予退款：
          </p>
          <ul>
            <li>对生成综述的质量或内容不满意</li>
            <li>不符合特定期望或要求的综述</li>
            <li>学术情况变化（例如，主题变更、项目取消）</li>
            <li>未能在到期前使用积分</li>
          </ul>
          <p className="policy-note">
            <strong>注意：</strong>我们在我们的网站上提供示例/演示案例，以便您在购买前
            评估我们服务的质量。我们建议您在购买前查看这些示例。
          </p>

          <h3>4.2 账户问题</h3>
          <p>
            以下情况不予退款：
          </p>
          <ul>
            <li>忘记密码或无法访问您的账户（我们提供账户恢复选项）</li>
            <li>因违反用户协议而被暂停的账户</li>
            <li>未能理解服务的基于积分的性质</li>
          </ul>

          <h3>4.3 学术后果</h3>
          <p>
            我们不对学术结果负责，包括但不限于：
          </p>
          <ul>
            <li>与我们服务生成内容相关的论文被拒</li>
            <li>学术诚信违规（用户负责正确署名）</li>
            <li>因服务中断而错过截止日期（我们努力保证正常运行时间，但不能保证 100% 可用性）</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>5. 积分过期</h2>

          <h3>5.1 过期政策</h3>
          <p>
            不同的积分套餐有不同的过期期限：
          </p>
          <ul>
            <li><strong>单次综述：</strong>积分不过期，但仅限一次性使用</li>
            <li><strong>学期套餐：</strong>积分自购买之日起 6 个月过期</li>
            <li><strong>学年套餐：</strong>积分自购买之日起 12 个月过期</li>
          </ul>

          <h3>5.2 过期积分</h3>
          <p>
            <strong>过期积分不能退款或延期。</strong>请相应地规划您的使用，
            并在选择套餐时考虑过期日期。
          </p>
        </section>

        <section className="legal-section">
          <h2>6. 服务修改与终止</h2>

          <h3>6.1 功能变更</h3>
          <p>
            我们不断改进我们的服务，这可能包括添加、修改或删除功能。
            由于不实质性影响核心功能的服务功能变更，
            将不予退款。
          </p>

          <h3>6.2 服务终止</h3>
          <p>
            在服务终止的不太可能发生的情况下，我们将提前至少 30 天通知。
            有有效积分的用户将有机会在关闭前使用剩余积分。
            我们可能会根据我们的唯一判断提供按比例退款。
          </p>
        </section>

        <section className="legal-section">
          <h2>7. 请求退款</h2>

          <h3>7.1 联系信息</h3>
          <p>
            要请求退款或报告技术问题，请联系我们：
            <br />
            <a href="mailto:service@snappicker.com" className="legal-link">
              service@snappicker.com
            </a>
          </p>

          <h3>7.2 所需信息</h3>
          <p>
            请在退款请求中包含以下信息：
          </p>
          <ul>
            <li>您的账户电子邮件地址</li>
            <li>订单/交易编号（来自您的收据）</li>
            <li>退款请求原因</li>
            <li>支持性文件（如适用）</li>
          </ul>

          <h3>7.3 处理时间</h3>
          <p>
            退款请求通常在 5-10 个工作日内审核。如果获得批准，退款将在
            14 个工作日内处理到原始付款方式。一旦您的退款已处理，
            我们将向您发送电子邮件确认。
          </p>

          <h3>7.4 技术问题</h3>
          <p>
            如果您遇到技术故障，导致无法使用服务（例如，综述
            生成失败、导出错误），请联系我们提供问题的详细信息。在调查问题后，
            我们可能会根据我们的判断提供积分替换或退款。
          </p>
        </section>

        <section className="legal-section">
          <h2>8. 拒付</h2>

          <h3>8.1 争议解决</h3>
          <p>
            我们鼓励您在向您的付款提供商发起拒付之前直接联系我们。
            许多问题可以通过直接沟通快速解决。
          </p>

          <h3>8.2 拒付后果</h3>
          <p>
            如果您在未先联系我们的情况下发起拒付，并且拒付被发现是
            不合法的（即服务已按描述交付），我们保留以下权利：
          </p>
          <ul>
            <li>收回有争议的金额加上处理费</li>
            <li>暂停或终止您的账户</li>
            <li>向付款处理商报告拒付为欺诈</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>9. 免费积分与促销</h2>

          <h3>9.1 促销积分</h3>
          <p>
            通过促销、推荐或特别优惠提供的免费积分没有现金价值，
            不能退款或兑换现金。
          </p>

          <h3>9.2 注册积分</h3>
          <p>
            注册时提供的 1 个免费积分供新用户试用服务。即使未使用，
            也不能退款或兑换。
          </p>
        </section>

        <section className="legal-section">
          <h2>10. 政策修改</h2>
          <p>
            我们保留随时修改本退款政策的权利。变更将在
            发布到网站后立即生效。变更后继续使用服务即
            表示接受新政策。
          </p>
          <p>
            重大变更将通过电子邮件或网站上的显著通知进行传达。
          </p>
        </section>

        <section className="legal-section">
          <h2>11. 联系信息</h2>
          <p>
            有关本退款政策或退款请求的问题：
            <br />
            <a href="mailto:service@snappicker.com" className="legal-link">
              service@snappicker.com
            </a>
            <br />
            <a href="mailto:support@snappicker.com" className="legal-link">
              support@snappicker.com
            </a>
          </p>
        </section>

        <footer className="legal-footer">
          <p>© 2026 AutoOverview. 保留所有权利。</p>
        </footer>
      </div>
    </div>
  )
}
