/**
 * Academic Integrity Policy Page - International Version
 */
import { Link } from 'react-router-dom'
import './LegalPages.css'

export function AcademicIntegrityPage() {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <Link to="/" className="legal-back-link">← Back to Home</Link>

        <h1 className="legal-title">Academic Integrity Policy</h1>
        <p className="legal-effective">Last Updated: April 19, 2026</p>

        <section className="legal-section">
          <h2>Our Commitment to Academic Integrity</h2>
          <p>
            Danmo Scholar is a <strong>literature discovery and organization tool</strong> designed to help
            researchers, graduate students, and scholars efficiently find, compare, and organize academic papers.
            We are committed to supporting ethical academic practices and responsible use of AI-assisted research tools.
          </p>
          <p>
            Our platform is comparable to established academic tools such as{' '}
            <a href="https://elicit.com" target="_blank" rel="noopener noreferrer">Elicit</a>,{' '}
            <a href="https://connectedpapers.com" target="_blank" rel="noopener noreferrer">Connected Papers</a>,{' '}
            and <a href="https://consensus.app" target="_blank" rel="noopener noreferrer">Consensus</a> —
            all of which assist researchers in navigating the vast academic literature landscape.
          </p>
        </section>

        <section className="legal-section">
          <h2>What Danmo Scholar Does</h2>
          <ul>
            <li><strong>Literature Search & Discovery</strong> — Search millions of academic papers via OpenAlex, one of the world's largest open academic databases</li>
            <li><strong>Paper Comparison</strong> — Compare methodologies, findings, and key metrics across multiple studies side-by-side</li>
            <li><strong>Citation Organization</strong> — Organize discovered papers with proper citation formatting (IEEE, APA, MLA, GB/T 7714) and export in BibTeX, RIS, or Word formats</li>
            <li><strong>Source Verification</strong> — Every paper result includes direct links to Google Scholar and DOI for verification against original sources</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>What Danmo Scholar Does NOT Do</h2>
          <ul>
            <li>We do <strong>not</strong> write essays, papers, or academic content on behalf of users</li>
            <li>We do <strong>not</strong> function as an essay mill, paper mill, or ghostwriting service</li>
            <li>We do <strong>not</strong> encourage or facilitate plagiarism</li>
            <li>We do <strong>not</strong> bypass academic writing requirements</li>
            <li>We do <strong>not</strong> replace critical thinking, original analysis, or scholarly judgment</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>Expected Use</h2>
          <p>
            Users are expected to use Danmo Scholar as a <strong>research aid</strong> — similar to how one would use
            a search engine, reference manager, or academic database. The organized literature and summaries provided
            by our tool are starting points for your own research, not finished academic products.
          </p>
          <p>
            We strongly encourage all users to:
          </p>
          <ul>
            <li>Read and critically evaluate all original papers referenced in results</li>
            <li>Verify information against primary sources using the provided Google Scholar and DOI links</li>
            <li>Add original analysis, synthesis, and critical perspectives to any literature review</li>
            <li>Follow their institution's academic integrity and citation policies</li>
            <li>Properly cite all sources in accordance with applicable citation standards</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>Prohibited Uses</h2>
          <p>
            The following uses of Danmo Scholar are strictly prohibited:
          </p>
          <ul>
            <li>Submitting AI-generated or AI-organized content as your own original academic work without proper attribution and substantial modification</li>
            <li>Using the tool to complete assignments, theses, or dissertations on behalf of another person</li>
            <li>Any form of academic dishonesty, including but not limited to plagiarism, fabrication, or misrepresentation</li>
            <li>Reselling or redistributing generated content as academic writing services</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>Enforcement</h2>
          <p>
            We reserve the right to suspend or terminate accounts that are used in violation of this Academic Integrity Policy.
            If we become aware that our tool is being used for academic misconduct, we will take appropriate action, including
            but not limited to account suspension and reporting to relevant institutions when required by law.
          </p>
        </section>

        <section className="legal-section">
          <h2>Contact</h2>
          <p>
            If you have questions about this policy or wish to report potential misuse, please contact us at{' '}
            <a href="mailto:support@danmoscholar.com">support@danmoscholar.com</a>.
          </p>
        </section>
      </div>
    </div>
  )
}
