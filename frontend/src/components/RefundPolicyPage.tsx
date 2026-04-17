/**
 * Refund Policy Page - International Version
 * Refund terms for AutoOverview SaaS service
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function RefundPolicyPage() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← Back to Home</Link>

        <h1 className="legal-title">Refund Policy</h1>
        <p className="legal-effective">Last Updated: April 12, 2026</p>

        <section className="legal-section">
          <h2>1. Overview</h2>
          <p>
            At AutoOverview, we strive to provide a high-quality AI-assisted literature review tool.
            This Refund Policy outlines the circumstances under which refunds may be issued.
            Please read this policy carefully before making a purchase.
          </p>
          <p className="policy-highlight">
            <strong>Important:</strong> AutoOverview is a low-frequency, essential academic SaaS tool.
            Due to the nature of AI-assisted content and immediate service delivery, refunds are handled
            differently than traditional products.
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Non-Refundable Purchases</h2>

          <h3>2.1 Consumed Credits</h3>
          <p>
            <strong>All used credits are non-refundable.</strong> Once a literature analysis has been generated
            using a credit, that credit cannot be refunded. This is because:
          </p>
          <ul>
            <li>AI processing costs are incurred immediately upon generation</li>
            <li>Academic database queries are performed in real-time</li>
            <li>The service delivers immediate value upon completion</li>
          </ul>

          <h3>2.2 Digital Content Delivery</h3>
          <p>
            Once a literature analysis has been generated and delivered to your account, the transaction is
            considered complete. Due to the nature of digital content and intellectual property considerations,
            we cannot offer refunds for completed analyses.
          </p>

          <h3>2.3 Subscription Credits</h3>
          <p>
            Purchased credit packages (Single, Semester, Academic Year) are non-refundable once any credit
            from that package has been used. Unused credits in a package cannot be refunded for cash.
          </p>
        </section>

        <section className="legal-section">
          <h2>3. Refund Eligibility</h2>

          <h3>3.1 Technical Failures</h3>
          <p>
            You may be eligible for a refund or credit replacement if:
          </p>
          <ul>
            <li>The service failed to generate an analysis due to a technical issue on our end</li>
            <li>The analysis was generated but contains critical formatting errors preventing export</li>
            <li>The service was unavailable for an extended period during your paid access period</li>
          </ul>
          <p>
            In these cases, we will investigate the issue and may offer a credit replacement or partial refund
            at our discretion.
          </p>

          <h3>3.2 Accidental Purchases</h3>
          <p>
            If you accidentally purchased a package and have not used any credits from it, contact us within
            <strong>7 days</strong> of purchase. We may issue a full refund if:
          </p>
          <ul>
            <li>No credits from the package have been used</li>
            <li>The request is made within 7 days of purchase</li>
            <li>You can demonstrate the accidental nature of the purchase</li>
          </ul>

          <h3>3.3 Duplicate Charges</h3>
          <p>
            If you were accidentally charged multiple times for the same purchase, we will refund the duplicate
            charges. Please contact us with your transaction details.
          </p>
        </section>

        <section className="legal-section">
          <h2>4. Non-Eligible Scenarios</h2>

          <h3>4.1 Dissatisfaction with Results</h3>
          <p>
            Refunds will not be issued for:
          </p>
          <ul>
            <li>Dissatisfaction with the quality or content of a generated analysis</li>
            <li>Analyses that do not meet specific expectations or requirements</li>
            <li>Changes in academic circumstances (e.g., topic change, project cancellation)</li>
          </ul>
          <p className="policy-note">
            <strong>Note:</strong> We provide sample/demo cases on our website so you can evaluate the quality
            of our service before making a purchase. We encourage you to review these examples before buying.
          </p>

          <h3>4.2 Account Issues</h3>
          <p>
            Refunds will not be issued for:
          </p>
          <ul>
            <li>Forgotten passwords or inability to access your account (we provide account recovery options)</li>
            <li>Account suspension due to violation of Terms & Conditions</li>
            <li>Failure to understand the credit-based nature of the service</li>
          </ul>

          <h3>4.3 Academic Consequences</h3>
          <p>
            We are not responsible for academic outcomes, including but not limited to:
          </p>
          <ul>
            <li>Paper rejections related to content generated by our AI-assisted tool</li>
            <li>Academic integrity violations (users are responsible for proper attribution)</li>
            <li>Deadlines missed due to service interruptions (we strive for uptime but cannot guarantee 100% availability)</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>5. Single Review Unlock Policy</h2>

          <h3>5.1 Unlock Purchases</h3>
          <p>
            When you purchase a single review unlock ($9.99), you are paying for the permanent removal of
            export restrictions on that specific review. Once unlocked:
          </p>
          <ul>
            <li>The unlock is permanent and non-reversible</li>
            <li>Refunds will not be issued for unlocked reviews</li>
            <li>If you accidentally unlocked the wrong review, contact us immediately—we may assist at our discretion</li>
          </ul>

          <h3>5.2 Already Unlocked Content</h3>
          <p>
            If you attempt to unlock a review that is already unlocked (e.g., through a previous purchase or
            credit usage), we cannot refund the duplicate purchase. Please verify a review's status before
            purchasing an unlock.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Service Modifications & Discontinuation</h2>

          <h3>7.1 Feature Changes</h3>
          <p>
            We continuously improve our service, which may include adding, modifying, or removing features.
            Refunds will not be issued due to changes in service features that do not substantially affect
            core functionality.
          </p>

          <h3>7.2 Service Discontinuation</h3>
          <p>
            In the unlikely event of service discontinuation, we will provide at least 30 days' notice.
            Users with active credits will be given the opportunity to use remaining credits before shutdown.
            Pro-rated refunds may be offered at our sole discretion.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Requesting a Refund</h2>

          <h3>7.1 Contact Information</h3>
          <p>
            To request a refund or report a technical issue, contact us at:
            <br />
            <a href="mailto:service@snappicker.com" className="legal-link">
              service@snappicker.com
            </a>
          </p>

          <h3>7.2 Required Information</h3>
          <p>
            Please include the following information in your refund request:
          </p>
          <ul>
            <li>Your account email address</li>
            <li>Order/transaction number (from your receipt)</li>
            <li>Reason for refund request</li>
            <li>Supporting documentation (if applicable)</li>
          </ul>

          <h3>7.3 Processing Time</h3>
          <p>
            Refund requests are typically reviewed within 5-10 business days. If approved, refunds will be
            processed to the original payment method within 14 business days. We will send you an email
            confirmation once your refund has been processed.
          </p>

          <h3>7.4 Technical Issues</h3>
          <p>
            If you experienced a technical failure that prevented you from using the service (e.g., review
            generation failed, export errors), please contact us with details of the issue. We may offer a
            credit replacement or refund at our discretion after investigating the issue.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Chargebacks</h2>

          <h3>8.1 Dispute Resolution</h3>
          <p>
            We encourage you to contact us directly before initiating a chargeback with your payment provider.
            Many issues can be resolved quickly through direct communication.
          </p>

          <h3>8.2 Chargeback Consequences</h3>
          <p>
            If you initiate a chargeback without contacting us first, and the chargeback is found to be
            illegitimate (i.e., the service was delivered as described), we reserve the right to:
          </p>
          <ul>
            <li>Reclaim the disputed amount plus processing fees</li>
            <li>Suspend or terminate your account</li>
            <li>Report the chargeback as fraudulent to payment processors</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>9. Free Credits & Promotions</h2>

          <h3>9.1 Promotional Credits</h3>
          <p>
            Free credits provided through promotions, referrals, or special offers have no cash value and
            cannot be refunded or exchanged for cash.
          </p>

          <h3>9.2 Registration Credits</h3>
          <p>
            The 1 free credit provided upon registration is for new users to try the service. It cannot be
            refunded or exchanged, even if not used.
          </p>
        </section>

        <section className="legal-section">
          <h2>10. Policy Modifications</h2>
          <p>
            We reserve the right to modify this Refund Policy at any time. Changes will be effective
            immediately upon posting to the website. Your continued use of the Service after changes
            constitutes acceptance of the new policy.
          </p>
          <p>
            Material changes will be communicated via email or prominent notice on the website.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. Understanding Our Service Model</h2>

          <h3>11.1 Low-Frequency, Essential Service</h3>
          <p>
            AutoOverview is designed as a low-frequency but essential AI-assisted tool for academic work. Unlike
            subscription services with recurring monthly charges, our credit-based model allows you to pay
            for what you need, when you need it.
          </p>

          <h3>11.2 Making Informed Decisions</h3>
          <p>
            To ensure satisfaction with your purchase:
          </p>
          <ul>
            <li>Review demo cases on our homepage</li>
            <li>Start with a Single Review package if you're new to the service</li>
            <li>Choose a package that matches your expected usage frequency</li>
          </ul>

          <h3>11.3 Quality Expectations</h3>
          <p>
            Our AI-assisted tool provides high-quality literature analysis drafts that serve as excellent research starting
            points. However, all AI-generated content must be reviewed, verified, and supplemented with your own
            original analysis and expertise before use in any academic context.
          </p>
        </section>

        <section className="legal-section">
          <h2>12. Contact Information</h2>
          <p>
            For questions about this Refund Policy or refund requests:
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
          <p>© 2026 AutoOverview. All rights reserved.</p>
        </footer>
      </div>
    </div>
  )
}
