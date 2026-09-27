# 🌾 Rural Micro-Enterprise AI Advisory & Financial Structuring Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant_%2B_FastEmbed-red.svg)](https://qdrant.tech/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-0088cc.svg)](https://core.telegram.org/bots/api)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API%20%2B%20Evolution-25D366.svg)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Test%20Suite-184%20Passed%20(100%25)-brightgreen.svg)]()

A production-ready, **100% zero-cost-tier** conversational AI advisory and financial structuring platform engineered to bridge the formal credit gap for hyper-local business owners and rural micro-entrepreneurs across India.

The platform operates natively on **Telegram** and **WhatsApp** (supporting spoken voice notes and text in **Kannada, Hindi, Telugu, Marathi, and English**). It deterministically structures subsidized government credit schemes, validates financial feasibility against **official NABARD unit-cost benchmarks**, compiles bank-ready **Detailed Project Report (DPR)** PDFs with 5-year cash-flow and DSCR projections, and provides State Channelizing Agency (SCA) field officers with a real-time geo-verification and loan sanction console.

---

## 📊 Real-Data Governance & Verification Status

The platform operates under strict **`REAL_DATA_ONLY=True`** governance. Factual financial and policy data is grounded exclusively in official Government of India, NABARD, and statutory corporation circulars. Every raw document is preserved in `data/raw/` and cryptographically tracked via **SHA-256 hashes** in `data/manifests/sources_manifest.json`.

### Verification Breakdown

| Component | Status | Official Source & Scope | Verified Implementation Details |
|---|---|---|---|
| **NABARD Unit Costs (8 Allied Activities)** | **`IMPLEMENTED`** | NABARD Karnataka RO State Level Unit Cost Committee (2026-27) | 12 verified SLUCC benchmarks: 2-Cow Dairy (₹2.29L/₹2.05L), Poultry Broiler (₹4.56L/₹20.80L), Sheep Rearing (₹1.11L/₹0.98L), Goat Rearing (₹1.13L/₹0.95L), Piggery (₹1.64L), Inland Fisheries (₹8.29L), Apiary Beekeeping (₹62.8K), and Sericulture (₹2.25L). |
| **Non-Farm Model Profile (Commercial Flour Mill)** | **`IMPLEMENTED`** | Project SAMADHAN / MDTC (2020) | Model pre-feasibility profile for commercial flour mill (2400 MT/yr, ₹32.93L total project cost, 12 employees). Explicitly labeled with 2020 vintage. |
| **PMEGP Scheme Policy Rules** | **`IMPLEMENTED`** | Ministry of MSME Operational Guidelines (2023) | Official ₹50L manufacturing / ₹20L service ceilings, 35%/25% rural margin money subsidies (5%/10% own equity), age ≥ 18, 8th-pass rule for projects > ₹5L, and negative list exclusions (kirana, raw trading). |
| **Statutory Corporation Schemes (NSFDC / NBCFDC / NSTFDC)** | **`IMPLEMENTED`** | Official Corporation Circulars & Patterns of Finance (2025/2026) | Direct demographic routing: Scheduled Castes → **NSFDC**, Backward Classes → **NBCFDC**, Scheduled Tribes → **NSTFDC** (including AMSY concessional loans for tribal women). |
| **PMMY / MUDRA Borrower Tiers** | **`IMPLEMENTED`** | PIB Notification & Ministry of Finance Circular (29.10.2024) | Official notified categories: Shishu (up to ₹50K), Kishore (₹50K–₹5L), Tarun (₹5L–₹10L), and **Tarun Plus (up to ₹20L)**. Bank-determined borrower share and interest rates. |
| **AIDIS Aggregate Credit Survey** | **`IMPLEMENTED`** | NSO NSS 77th Round Report No. 588 | Aggregate Karnataka & All-India credit statistics (Karnataka IOI 48.1%, National IOI 35.0%, 66.1% institutional debt share, AOD ₹59,748, DAR 3.8%). |
| **Unbenchmarked Trades (Kirana, Tailoring, etc.)** | **`ENFORCED REFUSAL`** | Absence of official NABARD farm cost data | **Anti-Hallucination Guardrail:** The system refuses to invent DSCR or cash flows. Leaves DSCR empty (`"Not available"`), omits ungrounded 5-year projections, and appends an audit notice to the DPR. |
| **Vector DB & FastEmbed Local RAG Layer** | **`IMPLEMENTED`** | Local Qdrant + FastEmbed `BAAI/bge-small-en-v1.5` | 100% self-hosted vector retrieval with 20 structured authoritative chunks, automatic collection verification/auto-rebuild, and zero external SaaS API fees. |

---

## 📑 Table of Contents

- [Executive Overview](#-executive-overview)
  - [The Rural Credit Problem](#the-rural-credit-problem)
  - [The AI Advisory Solution](#the-ai-advisory-solution)
  - [Key Platform Capabilities](#key-platform-capabilities)
- [Real-Data Governance & Verification Status](#-real-data-governance--verification-status)
- [System Architecture & Data Flow](#-system-architecture--data-flow)
- [Core Engineering Methodologies](#-core-engineering-methodologies)
  - [1. Deterministic Financial Math vs. Probabilistic LLM](#1-deterministic-financial-math-vs-probabilistic-llm)
  - [2. Zero-Assumption Conversational Intake Engine](#2-zero-assumption-conversational-intake-engine)
  - [3. Verified Social Category Scheme Routing](#3-verified-social-category-scheme-routing)
  - [4. Multilingual Script Isolation & Language Lock](#4-multilingual-script-isolation--language-lock)
  - [5. Zero-Cost Local Vector RAG Pipeline](#5-zero-cost-local-vector-rag-pipeline)
  - [6. High-Availability Multi-Channel Delivery](#6-high-availability-multi-channel-delivery)
  - [7. Dual-Engine Bank-Grade DPR PDF Generation](#7-dual-engine-bank-grade-dpr-pdf-generation)
  - [8. SCA Field Officer Console & Admin Analytics](#8-sca-field-officer-console--admin-analytics)
- [Mathematical Formulations](#-mathematical-formulations)
  - [RBI Reducing-Balance Annuity EMI](#rbi-reducing-balance-annuity-emi)
  - [Debt Service Coverage Ratio (DSCR)](#debt-service-coverage-ratio-dscr)
  - [Statutory Lending Tier Comparison](#statutory-lending-tier-comparison)
- [Repository Structure](#-repository-structure)
- [Installation & Quickstart Guide](#-installation--quickstart-guide)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Install Dependencies](#2-clone--install-dependencies)
  - [3. Environment Variables Configuration](#3-environment-variables-configuration)
  - [4. Running Automated Tests (184 Tests)](#4-running-automated-tests-184-tests)
  - [5. Launching the Field Officer Dashboard](#5-launching-the-field-officer-dashboard)
  - [6. Running the FastAPI Webhook & Polling Server](#6-running-the-fastapi-webhook--polling-server)
  - [7. Running via Docker Compose](#7-running-via-docker-compose)
- [Automated Test Suite Coverage](#-automated-test-suite-coverage)
- [Reliability, Security & Production Readiness](#-reliability-security--production-readiness)

---

## 🎯 Executive Overview

### The Rural Credit Problem
Rural micro-entrepreneurs (such as dairy farmers, kirana shopkeepers, tailors, rural artisans, and agro-processors) face severe systemic barriers when attempting to access formal credit:
1. **Financial Illiteracy & Documentation Barriers**: Compiling bankable Detailed Project Reports (DPRs), calculating Debt Service Coverage Ratios (DSCR), and structuring 5-year cash-flow statements typically requires hiring expensive intermediaries who exploit applicants.
2. **Language & Dialect Alienation**: National lending portals and scheme documentation (PMEGP, MUDRA) are published in formal English or standardized Hindi, excluding millions of vernacular speakers in southern and western India.
3. **Extortionate Informal Debt Trap**: Lacking formal banking collateral and structured documentation, rural traders frequently turn to local money-lenders charging usurious interest rates ($36\% - 60\%$ p.a.).
4. **SCA Verification Delays**: State Channelizing Agencies (SCAs) lack digitized, geo-tagged field-inspection pipelines to verify physical premises, project feasibility, and margin money deposits promptly.

### The AI Advisory Solution
The **Rural Micro-Enterprise AI Advisory Platform** delivers an end-to-end, zero-barrier financial structuring solution directly inside **Telegram** and **WhatsApp**:
- **Zero Typing Barrier**: Accepts natural spoken voice notes in native regional dialects and text.
- **Zero-Assumption Consultation**: Never guesses missing financial parameters; conversationally gathers trade, district, costs, demographics, and own equity in logical groups.
- **100% Deterministic Financial Precision**: Concessional loan structures, margin money, subsidies, reducing-balance amortizations, and DSCR metrics are calculated by a pure Python engine.
- **Bank-Concurring DPR Generation**: Instantly compiles and sends a vector-rendered, 2-page bankable DPR PDF directly to the applicant's chat.
- **Verified Demographic Scheme Optimization**: Automatically identifies and structures the most beneficial schemes (NSFDC, NBCFDC, NSTFDC AMSY, PMEGP, MUDRA).
- **Field Inspection Portal**: Syncs sanctioned proposals directly into an authenticated, geo-enabled Streamlit console for SCA officers.

### Key Platform Capabilities
- 🌐 **5 Native Languages**: Conversational intake, STT, TTS, scheme advisory, and DPR generation in **English, Hindi (हिंदी), Kannada (ಕನ್ನಡ), Telugu (తెలుగు), and Marathi (मराठी)**.
- 🎙️ **Voice In & Voice Out**: Spoken voice notes are transcribed with automated language synchronization, and responses include spoken audio synthesis.
- 🧮 **Deterministic Precision**: Zero LLM arithmetic; strict enforcement of statutory thresholds, loan ceilings, reducing-balance EMIs, and DSCR viability.
- 📄 **In-Chat PDF Delivery**: Bank-ready PDFs delivered directly into Telegram and WhatsApp chat streams without requiring external download links.
- 📍 **SCA Officer Console**: Streamlit dashboard featuring GPS coordinate logging, margin money verification, and one-click sanctioning.
- 📊 **Administrative Analytics & Controls**: Web portal featuring bot runtime controls, real-time KPI metrics, and multi-sheet Excel data export (`openpyxl`).

---

## 🏛️ System Architecture & Data Flow

```
                                  +---------------------------------------------------+
                                  |         Rural Micro-Entrepreneur (User)           |
                                  |   (Telegram Voice/Text | WhatsApp Voice/Text)     |
                                  +-------------------------+-------------------------+
                                                            |
                                                            | Inbound Update / Voice Note
                                                            v
                                  +---------------------------------------------------+
                                  |             Inbound Channel Controller            |
                                  |    - Telegram Polling Runner (Singleton Lock)     |
                                  |    - FastAPI Webhook (HMAC-SHA256 Idempotency)    |
                                  |    - Evolution API WhatsApp Webhook Adapter       |
                                  +-------------------------+-------------------------+
                                                            |
                             +------------------------------+------------------------------+
                             |                                                             |
                 (Voice Note .oga/.ogg)                                             (Text Message)
                             v                                                             v
            +----------------------------------+                          +----------------------------------+
            |      Voice STT Pipeline          |                          |   Multilingual Language Engine   |
            |  - Google Gemini 3.5 Flash Lite  |                          |  - Session Language Lock         |
            |  - Groq Whisper Audio Fallback   |                          |  - Indic Numeral Tokenizer       |
            +----------------+-----------------+                          +----------------+-----------------+
                             |                                                             |
                             +------------------------------+------------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |         Conversational State Machine              |
                                  |          (app/dialogue/intake.py)                 |
                                  |   - Grouped Questioning (Business, Bio, Money)    |
                                  |   - Zero-Assumption Parameter Validation          |
                                  |   - Summary Confirmation ("yes" / "ಹೌದು" / "हाँ") |
                                  +-------------------------+-------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |        Deterministic Statutory & Finance Engine   |
                                  |                  (app/finance/)                   |
                                  |  - NABARD SLUCC Unit Costs (12 Activity Models)   |
                                  |  - Category Quotas: SC (NSFDC), OBC (NBCFDC),     |
                                  |    ST (NSTFDC AMSY), General (PMEGP / MUDRA)      |
                                  |  - Reducing-Balance EMI & DSCR Derivations        |
                                  |  - Anti-Hallucination Guardrail (Refusal)         |
                                  +-------------------------+-------------------------+
                                                            |
                             +------------------------------+------------------------------+
                             |                                                             |
                             v                                                             v
            +----------------------------------+                          +----------------------------------+
            |      Local Vector RAG Layer      |                          |     DPR PDF Generation Engine    |
            |  - Qdrant (On-Disk Local DB)     |                          |  - ReportLab 4.1+ Vector Engine  |
            |  - FastEmbed BAAI/bge-small-en   |                          |  - 2-Page Official Bank Format   |
            |  - SHA-256 Verified Lineage      |                          |  - In-Chat File Stream Delivery  |
            +----------------+-----------------+                          +----------------+-----------------+
                             |                                                             |
                             +------------------------------+------------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |          SCA Field Officer Portal & Admin         |
                                  |  - Streamlit Inspection Dashboard (:8501)         |
                                  |  - FastAPI Administrative Web Console (:8000)     |
                                  |  - GPS Geotagging & Sanction Pipeline             |
                                  |  - Multi-Sheet Excel Analytics Export             |
                                  +---------------------------------------------------+
```

---

## ⚙️ Core Engineering Methodologies

### 1. Deterministic Financial Math vs. Probabilistic LLM
LLMs are probabilistic token generators; they cannot guarantee reproducible financial arithmetic or adhere to statutory legal rules. In this architecture:
- **LLM Isolation**: Google Gemini Flash Lite is strictly confined to natural language comprehension, colloquial dialogue extraction, and speech-to-text.
- **Pure Python Math**: All financial computations (own equity, subsidies, loan caps, reducing-balance amortizations, and DSCR metrics) are executed in pure Python based on official circulars. The LLM is **forbidden from calculating money or deciding loan eligibility**.

### 2. Zero-Assumption Conversational Intake Engine
Located in `app/dialogue/intake.py` and `app/dialogue/intake_parsing.py`, the intake engine replaces brittle single-prompt forms with a structured state machine:
- **Grouped Questioning**: Gathers details in logical conversational bundles:
  1. *Business Group*: enterprise trade, Karnataka district, project budget.
  2. *Personal Group*: applicant name, age, gender, social category.
  3. *Financial / Location Group*: village/town, annual family income, own contribution.
  4. *Policy Edge Checks*: ex-serviceman/disability (for general men), 8th-standard pass (for projects > ₹5 Lakh).
- **Rule-Based Pre-Parsing**: Regex parsers handle numbers, Indic currency amounts (e.g., `"2 lakh"`, `"ಎರಡು ಲಕ್ಷ"`, `"दो लाख"`), Indic numerals, and yes/no confirmations without calling the LLM unless dealing with unstructured text.
- **Mandatory Summary Confirmation**: The applicant hears/reads a full profile summary and must confirm (`"yes"` / `"ಹೌದು"` / `"हाँ"` or state corrections) before financial structuring begins.

### 3. Verified Social Category Scheme Routing
Rather than offering a generic, ungrounded scheme to every applicant, the engine in `app/finance/corporation_loans.py` and `app/finance/multi_schemes.py` routes applicants strictly according to their verified demographic profile:
- **Scheduled Castes (SC)**: Evaluated for **NSFDC** term loans (90% loan share at 6.5% / 8.0% interest).
- **Other Backward Classes (OBC)**: Evaluated for **NBCFDC** term loans (up to 85% loan share at 6.0% / 8.0% interest).
- **Scheduled Tribes (ST)**: Evaluated for **NSTFDC** term loans, including **AMSY (Adivasi Mahila Sashaktikaran Yojana)** offering 90% loan share at a highly concessional 4.0% interest for ST women with projects up to ₹1,00,000.
- **General Category**: Evaluated for **PMEGP** (15% urban / 25% rural margin money subsidy with 10% own equity) and **MUDRA (PMMY)**.
- **PMEGP Special Category**: SC, ST, OBC, Women, Ex-servicemen, and PwD receive 25% urban / 35% rural margin money subsidy with only 5% own equity.

### 4. Multilingual Script Isolation & Language Lock
- **Language Lock**: Resolves a major bug where typing Latin place names (e.g., `"Bengaluru"`) or brief greetings (`"Hi"`) caused regional conversations to flip back to English. Once selected, the user's language is strictly locked in the session until explicitly altered via menu.
- **Speech Synthesis Timeout**: External TTS calls (via `gTTS`) include strict 5-second socket timeout protection with automatic fallback to text, eliminating backend async deadlocks under poor network conditions.

### 5. Zero-Cost Local Vector RAG Pipeline
- **Zero Cloud Bill**: Runs 100% locally using **Qdrant** embedded on-disk storage and **FastEmbed** (`BAAI/bge-small-en-v1.5`) via ONNX Runtime.
- **Self-Healing Index**: `app/retrieval/service.py` detects missing or empty vector collections on fresh clones and automatically executes ingestion (`QDRANT_AUTO_INGEST=true`).
- **Cryptographic Provenance**: 20 authoritative policy chunks are registered with SHA-256 hashes in `data/manifests/sources_manifest.json`.

### 6. High-Availability Multi-Channel Delivery
- **Telegram Bot Daemon**: Uses long-polling with a local TCP socket mutex lock (`127.0.0.1:49153`) to prevent race conditions during daemon restarts.
- **WhatsApp Cloud API & Evolution API**: Supports official Meta Cloud webhooks with HMAC-SHA256 signature validation and an Evolution API adapter.

### 7. Dual-Engine Bank-Grade DPR PDF Generation
Implemented in `app/dpr/generator.py` using **ReportLab 4.1+**:
- **Vector-Sharp 2-Page Layout**: Generates a standard loan application document containing applicant profile, project cost breakdown, means of finance, 5-year repayment schedule, and DSCR metrics.
- **Zero Headless Browser Overhead**: Runs entirely in memory in under 50ms without headless Chromium or Puppeteer processes.
- **Anti-Hallucination Stamp**: For unbenchmarked trades (kirana, tailoring), DSCR is printed as `"Not available"`, the ungrounded 5-year table is omitted, and an official audit notice is displayed.

### 8. SCA Field Officer Console & Admin Analytics
- **Streamlit Inspector Dashboard (`:8501`)**: Authenticated portal for field officers to review pending applications, verify margin money deposits, record GPS coordinates, and approve loan sanctions.
- **FastAPI Admin Console (`:8000/admin`)**: Administrative console featuring bot start/stop toggles, system health monitors, and a multi-sheet Excel export engine (`/analytics/export/excel`) powered by `openpyxl`.

---

## 🧮 Mathematical Formulations

### RBI Reducing-Balance Annuity EMI
Term loans are amortized using the standard Reserve Bank of India reducing-balance formulation:

$$E = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

Where:
- $E$ = Monthly Equated Installment (EMI)
- $P$ = Principal Loan Amount
- $r$ = Monthly Interest Rate $\left(\frac{\text{Annual Rate}}{12 \times 100}\right)$
- $n$ = Loan Tenure in Months (typically 60 months / 5 years)

### Debt Service Coverage Ratio (DSCR)
Viability for bank credit is determined by calculating the Debt Service Coverage Ratio:

$$\text{DSCR} = \frac{\text{Net Operating Income} + \text{Depreciation}}{\text{Total Debt Service (Annual Principal + Interest)}}$$

- **Viable Benchmark**: $\text{DSCR} \ge 1.50$ indicates healthy debt repayment capacity.
- **Enforced Refusal**: If official NABARD benchmark cash-flows do not exist for the trade, DSCR is set to `None` / `"Not available"` rather than hallucinating an arbitrary figure.

### Statutory Lending Tier Comparison

| Metric / Parameter | PMEGP (General) | PMEGP (Special Category) | NSFDC / NBCFDC Term Loan | NSTFDC AMSY (Tribal Women) | MUDRA (PMMY) |
|---|---|---|---|---|---|
| **Beneficiary Focus** | General Rural/Urban | SC, ST, OBC, Women, PwD | Scheduled Castes / OBC | Scheduled Tribes (Women) | Micro Enterprises |
| **Max Project Cost** | ₹50L (Mfg) / ₹20L (Svc) | ₹50L (Mfg) / ₹20L (Svc) | ₹50 Lakhs | Up to ₹1,00,000 | Up to ₹20 Lakhs |
| **Own Contribution** | **10%** | **5%** | **5% – 15%** | **10%** (Max) | Nil / Bank Norms |
| **Government Subsidy** | 15% (U) / 25% (R) | **25% (U) / 35% (R)** | Interest Subvention | Interest Subvention | Nil (Subvention only) |
| **Interest Rate** | Commercial Bank Rate | Commercial Bank Rate | **6.0% – 8.0% p.a.** | **4.0% p.a.** | Commercial Bank Rate |
| **Collateral** | Collateral-Free (CGTMSE) | Collateral-Free (CGTMSE) | State Govt Guarantee / SCA | SCA Guarantee | Collateral-Free (CGFMU) |

---

## 📂 Repository Structure

```text
Rural Advisory/
├── app/
│   ├── ai/
│   │   ├── advisory_text.py         # Deterministic multilingual scheme advisory templates
│   │   ├── extraction.py            # Free-form entity extraction & dialogue classification
│   │   ├── gemini_client.py         # Google Gemini Flash Lite client (text & multimodal audio)
│   │   └── pmegp_text.py            # Multilingual PMEGP eligibility notices & advice
│   ├── auth/
│   │   ├── routes.py                # Authentication routes (/login, /logout, /me)
│   │   └── security.py              # Password hashing (PBKDF2) & JWT session cookies
│   ├── db/
│   │   ├── crud.py                  # Database operations & default account seeding
│   │   ├── models.py                # SQLAlchemy 2.0 models (Beneficiary, Proposal, User, Snapshot)
│   │   └── session.py               # SQLite WAL connection & session factory
│   ├── dialogue/
│   │   ├── conversation_state.py    # Master session state machine & workflow controller
│   │   ├── intake.py                # Grouped intake question orchestration & validation
│   │   ├── intake_parsing.py        # Rule-based Indic numerals, amounts, and affirmative readers
│   │   └── intake_text.py           # 5-language localized prompts for each intake group
│   ├── dpr/
│   │   ├── generator.py             # ReportLab 4.1+ vector PDF DPR generation engine
│   │   └── templates/               # HTML fallbacks & PDF layout styling
│   ├── finance/
│   │   ├── benchmarks.py            # NABARD Karnataka SLUCC trade models & parameters
│   │   ├── corporation_loans.py     # NSFDC, NBCFDC, and NSTFDC category routing & loan math
│   │   ├── formatting.py            # Indian Rupee formatting utilities (lakh, crore, INR)
│   │   ├── multi_schemes.py         # Multi-scheme financial structuring & comparison
│   │   ├── pmegp.py                 # PMEGP operational guidelines & subsidy calculator
│   │   └── repository.py            # Benchmark retrieval & financial data access
│   ├── retrieval/
│   │   ├── context_builder.py       # RAG context assembler with source citations
│   │   ├── ingest.py                # Local Qdrant FastEmbed ingestion pipeline
│   │   ├── models.py                # Pydantic schemas for retrieved evidence & metadata
│   │   ├── router.py                # Keyword & semantic retrieval router
│   │   └── service.py               # Qdrant client, auto-rebuild check & search guardrails
│   ├── telegram/
│   │   ├── bot_client.py            # Telegram Bot API client & PDF file delivery
│   │   └── webhook_handler.py       # Telegram webhook & update dispatcher
│   ├── voice/
│   │   └── voice_service.py         # Gemini 3.5 Audio STT + Groq Whisper + gTTS synthesis
│   ├── whatsapp/
│   │   ├── client.py                # Meta WhatsApp Cloud API client
│   │   ├── evolution_client.py      # WhatsApp Evolution API adapter
│   │   └── webhook_handler.py       # WhatsApp webhook handler with HMAC signature validation
│   ├── analytics.py                 # Multi-district application analytics aggregator
│   ├── analytics_export.py          # Multi-sheet Excel export generator (openpyxl)
│   ├── bot_control.py               # Telegram & WhatsApp bot runtime state manager
│   ├── config.py                    # Pydantic Settings & environment configuration
│   └── main.py                      # FastAPI application entry point, lifecycle & admin console
├── dashboard/
│   └── streamlit_app.py             # SCA Field Officer inspection console (:8501)
├── data/
│   ├── manifests/
│   │   └── sources_manifest.json    # Cryptographic SHA-256 data provenance registry
│   ├── processed/
│   │   ├── aidis/                   # Processed NSS 77th Round debt survey statistics
│   │   ├── nabard/                  # 12 verified SLUCC Karnataka activity models
│   │   ├── non_farm/                # MDTC commercial flour mill profile
│   │   ├── schemes/                 # JSON rule sets: NSFDC, NBCFDC, NSTFDC, PMEGP, MUDRA
│   │   └── retrieval_chunks.json    # 20 pre-indexed authoritative policy chunks
│   └── raw/schemes/                 # Preserved official HTML source files for statutory schemes
├── docs/                            # Deep technical architecture, audit, and baseline documents
├── scripts/
│   ├── evaluate_retrieval.py        # 23-query RAG precision evaluation benchmark
│   ├── generate_defense_dossier_pdf.py # ReportLab technical defense dossier PDF generator
│   └── run_telegram_polling.py      # Standalone Telegram long-polling runner with singleton lock
├── tests/                           # Complete automated test suite (184 tests, 100% passing)
├── docker-compose.yml               # Multi-container orchestration (FastAPI + Qdrant)
├── Dockerfile                       # Production container build specification
├── requirements.txt                 # Project Python dependencies
├── .env.example                     # Environment configuration template
└── README.md                        # Master project documentation
```

---

## 🚀 Installation & Quickstart Guide

### 1. Prerequisites
- **Python 3.10 to 3.14**
- A **Google Gemini API Key** (Free Tier from [Google AI Studio](https://aistudio.google.com/))
- *(Optional)* A **Telegram Bot Token** (from `@BotFather`) to test live messaging

### 2. Clone & Install Dependencies

```bash
git clone https://github.com/chinmay-workdesign/Rural-Enterprise-Advisor.git
cd Rural-Enterprise-Advisor

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env`:

```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS
```

Configure your credentials in `.env`:

```env
# Google Gemini API Key (Free tier from aistudio.google.com)
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_AUDIO_MODEL=gemini-3.5-flash-lite

# Telegram Bot API Token (Optional, from @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Real-Data Governance (Default: true)
REAL_DATA_ONLY=true

# Database URL (Defaults to local SQLite WAL database)
DATABASE_URL=sqlite:///./rural_advisor.db
```

### 4. Running Automated Tests (184 Tests)

Run the full automated test suite:

```bash
python -m pytest tests/ -v
```

Expected result:
```text
====================== 184 passed, 5 warnings in 15.94s =======================
```

### 5. Launching the Field Officer Dashboard

Start the Streamlit inspection console:

```bash
streamlit run dashboard/streamlit_app.py --server.port 8501
```

Navigate to **[http://localhost:8501](http://localhost:8501)**.  
* **Field Officer Demo:** `officer.belagavi@sca.gov.in` / `Officer@123`  
* **State Admin Demo:** `admin@sca.gov.in` / `Admin@123`

### 6. Running the FastAPI Webhook & Polling Server

Start the core backend server:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Administrative Console:** **[http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)**
- **Interactive API Docs (Swagger):** **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
- **Integrated Telegram Bot:** If `TELEGRAM_BOT_TOKEN` is present, long-polling starts automatically in a background daemon thread with singleton port locking.

### 7. Running via Docker Compose

Deploy the complete containerized stack:

```bash
docker compose up -d --build
```

---

## 🧪 Automated Test Suite Coverage

The platform maintains **184 automated tests** with 100% pass rate across 20 specialized test modules:

```text
tests/
├── e2e/
│   ├── test_channels_and_voice.py          (13 tests) - Polling lock, WhatsApp HMAC, voice roundtrip
│   ├── test_data_lineage_traceability.py    (3 tests) - SHA-256 hash validation to raw source docs
│   ├── test_dpr_real_data_provenance.py     (3 tests) - Real-data grounding in DPR PDF output
│   ├── test_failure_injection.py           (10 tests) - Fault tolerance: LLM offline, corrupted audio
│   ├── test_llm_financial_integrity.py      (9 tests) - Proves zero LLM math hallucination
│   └── test_real_world_flows.py            (12 tests) - End-to-end multi-turn flows across 5 languages
├── test_analytics.py                        (3 tests) - Multi-tab Excel export & district metrics
├── test_auth.py                            (10 tests) - RBAC roles, password hashing, session cookies
├── test_authoritative_retrieval.py         (26 tests) - Qdrant search precision & citation verification
├── test_benchmark_repository.py            (15 tests) - NABARD unit costs & activity models
├── test_bot_control.py                      (4 tests) - Telegram & Evolution API runtime toggles
├── test_category_schemes.py                 (8 tests) - NSFDC, NBCFDC, NSTFDC category routing
├── test_collection_readiness.py             (2 tests) - Qdrant collection validation & auto-rebuild
├── test_dialogue_state.py                   (5 tests) - State transitions & session language locking
├── test_dpr_generation.py                   (2 tests) - ReportLab PDF layout & 5-year cash flows
├── test_finance_calculator.py               (6 tests) - Reducing-balance EMI math & DSCR formulations
├── test_intake_no_assumptions.py           (16 tests) - Grouped intake, Indic numerals, zero guesses
├── test_real_data_financial_engine.py      (16 tests) - PMEGP subsidy slabs & statutory loan shares
├── test_real_data_only_flow.py              (5 tests) - Enforced refusal on unbenchmarked trades
├── test_telegram_channel.py                 (3 tests) - Telegram keyboard & chunked text handling
├── test_voice_pipeline.py                   (4 tests) - Gemini STT + Groq Whisper failover
├── test_webhook_parsing.py                  (4 tests) - WhatsApp Cloud API payload normalization
└── test_whatsapp_evolution.py               (5 tests) - Evolution API message serialization
========================================================================================
TOTAL: 184 Passed, 0 Failed (100% Coverage)
```

---

## 🔒 Reliability, Security & Production Readiness

1. **Deterministic Execution**: Pure Python execution for all financial calculations eliminates token variation, non-deterministic math, and prompt injection attacks on financial metrics.
2. **Cryptographic Data Provenance**: Every benchmark cites its raw document origin, page reference, and SHA-256 hash.
3. **Session Language Lock**: Prevents script leakage, ensuring vernacular speakers never have their consultation unexpectedly reverted to English.
4. **Offline Resilience**: Runs 100% locally with embedded SQLite (WAL) and on-disk Qdrant. No external vector database or embedding API accounts required.
5. **Role-Based Security**: Administrative console and Field Officer console are protected by PBKDF2 password hashing, HTTP-only secure session cookies, and strict route guards.
6. **Graceful Degradation**: Multi-tier audio fallback (Gemini 3.5 Audio → Groq Whisper → Raw Text) guarantees consultation continuity even during third-party API disruptions.

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
