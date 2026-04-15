/**
 * Privacy Policy Page - International Version
 * Privacy practices for AutoOverview SaaS service
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function PrivacyPolicyPage() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← Back to Home</Link>

        <h1 className="legal-title">Privacy Policy</h1>
        <p className="legal-effective">Last Updated: April 12, 2026</p>

        <section className="legal-section">
          <h2>1. Introduction</h2>
          <p>
            AutoOverview ("we," "our," or "us") respects your privacy and is committed to protecting your
            personal data. This privacy policy explains how we collect, use, disclose, and safeguard your
            information when you use our AI-assisted literature review tool.
          </p>
          <p>
            Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy,
            please do not access the Service.
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Data We Collect</h2>

          <h3>2.1 Personal Information</h3>
          <p>We collect information that you provide directly to us:</p>
          <ul>
            <li><strong>Account Information:</strong> Name, email address, and academic affiliation</li>
            <li><strong>Payment Information:</strong> Processed securely through PayPal (we do not store credit card details)</li>
            <li><strong>Research Topics:</strong> The subjects you enter for literature analysis</li>
            <li><strong>Generated Content:</strong> Analysis drafts and citations generated through the Service</li>
          </ul>

          <h3>2.2 Automatically Collected Information</h3>
          <p>We automatically collect certain information when you use the Service:</p>
          <ul>
            <li><strong>Usage Data:</strong> Pages viewed, features used, time spent, frequency of access</li>
            <li><strong>Device Information:</strong> Browser type, operating system, IP address</li>
            <li><strong>Log Data:</strong> Access times, pages visited, errors encountered</li>
          </ul>

          <h3>2.3 Cookies and Tracking</h3>
          <p>
            We use cookies and similar technologies to improve your experience, analyze usage patterns, and
            for security purposes. You can manage cookie preferences through your browser settings.
          </p>
        </section>

        <section className="legal-section">
          <h2>3. How We Use Your Data</h2>
          <p>We use the collected data for the following purposes:</p>

          <h3>3.1 Service Delivery</h3>
          <ul>
            <li>Process and generate literature analysis drafts based on your research topics</li>
            <li>Manage your account and credits</li>
            <li>Provide customer support</li>
            <li>Send transactional emails (receipts, usage notifications)</li>
          </ul>

          <h3>3.2 Service Improvement</h3>
          <ul>
            <li>Analyze usage patterns to improve AI model accuracy</li>
            <li>Identify and fix technical issues</li>
            <li>Develop new features and services</li>
          </ul>

          <h3>3.3 Security & Fraud Prevention</h3>
          <ul>
            <li>Detect and prevent fraudulent activity</li>
            <li>Protect against unauthorized access</li>
            <li>Verify user identity</li>
          </ul>

          <h3>3.4 Communications</h3>
          <ul>
            <li>Send product updates and educational content (you can opt-out)</li>
            <li>Respond to your inquiries and support requests</li>
            <li>Notify you of important service changes</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>4. Data Sharing & Disclosure</h2>

          <h3>4.1 Third-Party Service Providers</h3>
          <p>We share data with trusted third parties who assist us in operating the Service:</p>
          <ul>
            <li><strong>Payment Processing:</strong> PayPal processes payments. We do not store your credit card information.</li>
            <li><strong>Academic Databases:</strong> We query public academic APIs (Semantic Scholar, IEEE, etc.) to retrieve papers.</li>
            <li><strong>Cloud Infrastructure:</strong> AWS and similar providers host our services.</li>
            <li><strong>Analytics:</strong> We use analytics tools to understand usage patterns.</li>
          </ul>

          <h3>4.2 No Sale of Personal Data</h3>
          <p>
            We do not sell, rent, or trade your personal information. Your research topics and generated content
            are not sold to third parties.
          </p>

          <h3>4.3 Legal Requirements</h3>
          <p>
            We may disclose your information if required to do so by law or in response to valid legal requests
            from law enforcement or other government authorities.
          </p>

          <h3>4.4 Business Transfers</h3>
          <p>
            In the event of a merger, acquisition, or sale of assets, your data may be transferred to the
            new owner.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Data Retention</h2>

          <h3>5.1 Account Data</h3>
          <p>
            We retain your account information and generated reviews for the duration of your account and for
            a reasonable period after account closure for legal and operational purposes.
          </p>

          <h3>5.2 Usage Data</h3>
          <p>
            Anonymized usage data may be retained indefinitely for analytics and service improvement purposes.
          </p>

          <h3>5.3 Data Deletion</h3>
          <p>
            You may request deletion of your personal data by contacting us. We will delete your data within
            30 days, subject to legal retention requirements.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Academic Content & Research Topics</h2>

          <h3>6.1 Confidentiality</h3>
          <p>
            Your research topics and generated analysis drafts are stored securely and are not publicly accessible
            through your account. We do not use your unpublished research to train our models without consent.
          </p>

          <h3>6.2 AI Data Processing</h3>
          <p>
            We process your research topics and uploaded literature solely to generate AI-assisted analysis content.
            We do not store complete copies of your uploaded literature. Generated content is created in real-time
            and remains under your control.
          </p>

          <h3>6.3 Content Ownership</h3>
          <p>
            You retain ownership of all analysis drafts generated through the Service. We do not retain any ownership
            rights to your generated content. However, you acknowledge that content is AI-assisted and must be
            reviewed and supplemented with your own original work.
          </p>

          <h3>6.4 Model Training</h3>
          <p>
            We may use anonymized and aggregated data to improve our AI models. This data does not include
            personally identifiable information or specific research content that could identify you.
          </p>

          <h3>6.5 Public vs. Private Content</h3>
          <p>
            Only you can access the analysis drafts generated through your account. Demo cases shown on our website
            are either explicitly marked as examples or shared with user consent.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Data Security</h2>
          <p>We implement appropriate security measures to protect your information:</p>
          <ul>
            <li><strong>Encryption:</strong> Data is encrypted in transit and at rest</li>
            <li><strong>Access Controls:</strong> Limited access to personal data</li>
            <li><strong>Regular Audits:</strong> Periodic security assessments</li>
            <li><strong>Secure Payments:</strong> PCI-compliant payment processing through PayPal</li>
          </ul>
          <p>
            Despite our efforts, no method of transmission over the Internet is 100% secure. While we strive
            to protect your data, we cannot guarantee absolute security.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Your Rights & Choices</h2>
          <p>Depending on your location, you may have the following rights:</p>

          <h3>8.1 Account Closure</h3>
          <p>
            You can close your account at any time through your profile settings. Upon closure:
          </p>
          <ul>
            <li>Your account will be marked as inactive immediately</li>
            <li>All access to your reviews and credits will be revoked</li>
            <li>Your data will be scheduled for permanent deletion within 30 days</li>
            <li>You can request account reactivation within the 30-day period by contacting support</li>
          </ul>

          <h3>8.2 Data Deletion</h3>
          <p>
            You may request deletion of your personal data at any time by contacting us at
            privacy@autooverview.snappicker.com. We will process your request within 30 days, subject to
            legal retention requirements. Upon request, we will delete:
          </p>
          <ul>
            <li>Your account information and profile data</li>
            <li>All generated analysis drafts and associated content</li>
            <li>Research topics and query history</li>
            <li>Payment records (as permitted by law)</li>
          </ul>

          <h3>8.3 Data Access & Portability</h3>
          <p>
            You can request a copy of your personal data by contacting us at privacy@autooverview.snappicker.com.
            We will provide your data in a structured format within 30 days.
          </p>

          <h3>8.4 Data Correction</h3>
          <p>
            To update or correct inaccurate information, please contact us at support@snappicker.com with
            the details of the information you wish to change.
          </p>

          <h3>8.5 Objection & Opt-Out</h3>
          <p>
            You can object to certain data processing activities or opt-out of marketing communications
            by contacting us at privacy@autooverview.snappicker.com.
          </p>
        </section>

        <section className="legal-section">
          <h2>9. Children's Privacy</h2>
          <p>
            The Service is intended for users who are at least 13 years old. We do not knowingly collect
            personal information from children under 13. If you are a parent or guardian and believe your
            child has provided us with personal data, please contact us.
          </p>
        </section>

        <section className="legal-section">
          <h2>10. International Data Transfers</h2>
          <p>
            Your information may be transferred to and processed in countries other than your own. We ensure
            appropriate safeguards are in place to protect your data in accordance with this Privacy Policy
            and applicable laws.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. California Residents (CCPA)</h2>
          <p>If you are a California resident, you have specific rights regarding your personal information:</p>
          <ul>
            <li>Right to know what personal information is collected</li>
            <li>Right to know if personal information is sold or disclosed</li>
            <li>Right to opt-out of the sale of personal information</li>
            <li>Right to equal service and price</li>
          </ul>
          <p>
            To exercise these rights, please contact us at privacy@autooverview.snappicker.com
          </p>
        </section>

        <section className="legal-section">
          <h2>12. EU Residents (GDPR)</h2>
          <p>If you are an EU resident, you have additional rights under GDPR:</p>
          <ul>
            <li>Right to a copy of your personal data</li>
            <li>Right to rectification</li>
            <li>Right to erasure ("right to be forgotten")</li>
            <li>Right to restrict processing</li>
            <li>Right to data portability</li>
            <li>Right to object to processing</li>
            <li>Right to lodge a complaint with a supervisory authority</li>
          </ul>
          <p>
            Our legal basis for processing includes: consent, contract performance, legal obligation, and
            legitimate interests.
          </p>
        </section>

        <section className="legal-section">
          <h2>13. Updates to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of significant changes
            via email or through the Service. Your continued use after changes constitutes acceptance of
            the updated policy.
          </p>
        </section>

        <section className="legal-section">
          <h2>14. Contact Information</h2>
          <p>
            For questions about this Privacy Policy or your personal data, please contact us at:
            <br />
            <a href="mailto:privacy@autooverview.snappicker.com" className="legal-link">
              privacy@autooverview.snappicker.com
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
