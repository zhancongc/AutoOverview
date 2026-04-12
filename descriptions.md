# AutoOverview — Product Delivery Description

## What Is AutoOverview

AutoOverview is an AI-powered literature review generation platform. Users input a research topic, and the system automatically searches academic papers and generates a well-structured, properly cited academic literature review in minutes.

---

## How the Product Is Delivered

### Step 1: User Lands on the Website

- **Chinese version**: autooverview.snappicker.com — serves China's academic users
- **English version**: autooverview.plainkit.top — serves international markets (US, UK, Canada, EU)
- Fully bilingual UI with real-time language switching
- Clean landing page with a prominent topic input field, pricing cards, and feature highlights

### Step 2: User Signs Up / Logs In

- Verification-code login (email or phone) — no password required
- Account is created instantly; **1 free review credit** is granted on signup
- JWT-based authentication for all subsequent API calls

### Step 3: User Purchases Credits (Optional)

Users can generate 1 free review, then purchase additional credits:

| Plan | Chinese (CNY) | English (USD) | Credits |
|---|---|---|---|
| Starter / 单次 | ¥39.8 | $5.99 | 1 |
| Semester Pro / 学期包 | ¥119.4 | $27.99 | 12 |
| Annual Premium / 学年包 | ¥238.8 | $64.99 | 36 |

- **Chinese users** pay via Alipay QR code scan
- **International users** pay via Paddle (credit card, Apple Pay, etc.)
- Credits never expire; no subscription required

### Step 4: User Submits a Research Topic

- User types a research topic (e.g. "Transformer models in medical imaging") into the input field
- 1 credit is deducted immediately upon submission
- A background task is created and a task ID is returned

### Step 5: AI Pipeline Generates the Review (3-Stage Pipeline)

**Stage 1 — Paper Search (PaperSearchAgent)**
- LLM + Function Calling drives the search via Semantic Scholar API
- Searches across recent academic publications (default: last 10 years)
- Filters papers by citation count, recency, and relevance
- Collects at least 20 relevant papers with full metadata (title, authors, abstract, citations, year)

**Stage 2 — Review Generation (SmartReviewGeneratorFinal)**
- Uses DeepSeek (deepseek-reasoner) to synthesize a comprehensive literature review
- Applies 5 strict citation rules:
  1. No citations to papers not in the reference list
  2. All cited papers appear in the reference list
  3. Citation numbers increment sequentially from [1]
  4. No single paper is cited more than twice
  5. No uncited papers remain in the reference list
- Outputs a structured academic review in Markdown

**Stage 3 — Citation Validation (CitationValidatorV2)**
- Validates citation integrity and formatting
- Fixes any broken references or formatting issues
- Ensures proper IEEE/APA/MLA/GB T 7714 formatting

**Progress Tracking**:
- Real-time progress bar with stage labels: Searching → Analyzing → Generating → Validating → Complete
- Adaptive polling (starts at 20s intervals, accelerates to 8s near completion)
- Task state persists — user can close the browser and return later

### Step 6: User Receives the Completed Review

The finished review is presented in an interactive web viewer:

- **Content tab**: Full review with auto-generated Table of Contents sidebar
- **References tab**: All cited papers with metadata
- **Citation tooltips**: Hover over any [n] citation to see paper details
- **Reference format switching**: IEEE / APA / MLA / GB T 7714 — one click to switch
- **Heading normalization**: Automatic heading level correction for consistent structure

### Step 7: User Exports the Review

**Word Export** (.docx):
- Server-side generation via python-docx
- Professional academic formatting with selected citation style
- Requires a paid plan or one-time unlock ($9.99 / ¥39.8)

---

## Technical Architecture

```
User Browser (React + TypeScript)
    ↓ Vite build + i18n
    ↓ Hash routing (/#/login, /#/review, /#/pricing)
    ↓ API proxy → backend
    ↓
FastAPI Backend (Python)
    ├── main.py — all API routes, middleware, credit checks
    ├── PaperSearchAgent — Semantic Scholar search
    ├── SmartReviewGeneratorFinal — DeepSeek review generation
    ├── CitationValidatorV2 — citation validation & fix
    ├── TaskManager — async task polling & status
    └── AuthKit — auth, payments, credits, stats
    ↓
PostgreSQL (reviews + users)
Redis (task state + statistics)
```

---

## Deployment

- **Chinese site**: Shanghai server, Caddy/Nginx reverse proxy, Alipay integration
- **International site**: New York server, Caddy/Nginx reverse proxy, Paddle integration
- HTTPS via Cloudflare wildcard certificates
- Separate frontend builds per locale (`dist-zh` / `dist-en`)
- Automated deployment scripts (`deploy-zh.sh`, `deploy-en.sh`)

---

## Key Value Propositions

1. **Speed**: A full literature review in ~3-5 minutes vs. days of manual work
2. **Quality**: Multi-stage AI pipeline with strict citation validation
3. **Academic standards**: Proper IEEE/APA/MLA/GB T 7714 formatting
4. **No subscription**: Pay per use, credits never expire
5. **Bilingual**: Full Chinese and English support with locale-specific pricing and payments
6. **Professional export**: Word (.docx) with academic formatting
