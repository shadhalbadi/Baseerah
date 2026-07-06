# Baseerah — Project Proposal

**AI-Powered Utility Consumption Intelligence Platform**

*Analyzing water & electricity bills to detect anomalies, surface leaks and inefficiencies, and deliver personalized savings recommendations.*

| | |
|---|---|
| **Prepared by** | Shadha |
| **Document version** | 1.0 |
| **Date** | 5 July 2026 |
| **Status** | Draft for review |

---

## 1. Executive Summary

**Baseerah** (Arabic: بصيرة — *insight/discernment*) is an AI-powered web application that turns raw water and electricity bills into actionable intelligence. Households and small businesses regularly overpay for utilities without knowing why: a silent water leak, an aging appliance, a mispriced tariff tier, or a seasonal spike that never gets questioned. Utility bills report *what* was consumed, but never *why* — and never what to do about it.

Baseerah closes that gap. Users upload or connect their bills, and the platform:

- **Detects unusual consumption patterns** using anomaly-detection models trained on the user's own history plus peer cohorts.
- **Flags probable leaks and inefficiencies** (e.g. continuous overnight water flow, a device drawing standby power, a compressor running longer than it should).
- **Forecasts upcoming usage and cost** so there are no bill-shock surprises.
- **Delivers personalized, prioritized recommendations** ranked by estimated savings and effort.

The outcome for the user: lower bills, fewer emergencies, and a clear understanding of where their money and resources are going. The outcome for the region: measurable reductions in water and energy waste — directly aligned with Oman Vision 2040 sustainability goals and GCC water-security priorities.

**The ask:** approval to proceed with a Phase 1 MVP (see §12 Roadmap) targeting a validated pilot within [X] months.

---

## 2. Problem Statement

### 2.1 The user's problem
- **Bills are opaque.** A monthly total and a consumption number tell the user nothing about *what changed* or *what's normal*.
- **Leaks and faults are invisible until they're expensive.** A dripping connection or a running toilet can waste thousands of liters before anyone notices — often only when the bill arrives.
- **No personalized guidance exists.** Generic "turn off the lights" advice ignores the user's actual usage profile, tariff structure, climate, and appliances.
- **No forward visibility.** Users react to bills; they never anticipate them.

### 2.2 The regional context
- Oman and the wider GCC face among the **highest per-capita water and electricity consumption** in the world, combined with heavy reliance on energy-intensive desalination.
- Subsidy reform has made utility costs increasingly visible to end users, raising demand for cost-control tools.
- Sustainability targets (Oman Vision 2040) create both policy tailwind and potential institutional customers (utilities, municipalities, ESG-focused enterprises).

### 2.3 Why now
- Utilities are digitizing billing (PDF/e-bills, and increasingly smart-meter data via APIs), making the raw data accessible.
- Modern ML makes accurate per-household anomaly detection and forecasting feasible at low cost.
- Growing cost-consciousness and environmental awareness create genuine pull.

---

## 3. Solution Overview

Baseerah is a web application (responsive, mobile-first) with an optional future mobile app. The core loop:

```
  Ingest bills  →  Normalize & enrich  →  Analyze (AI/ML)  →  Insight & action
  (upload/API)     (parse, structure)     (anomaly,           (alerts, forecasts,
                                            forecast,           recommendations,
                                            diagnosis)          tips)
```

### 3.1 Core capabilities

1. **Bill ingestion** — upload PDF/image bills (OCR), manual entry, or direct utility-account connection where APIs exist.
2. **Consumption analysis** — establish each user's baseline, detect statistically significant deviations, and classify them (seasonal vs. anomalous).
3. **Leak & inefficiency detection** — apply domain heuristics + ML to distinguish "you used more" from "something is wrong" (leak, fault, standby drain, tariff mismatch).
4. **Usage & cost forecasting** — predict next-period consumption and cost, with confidence ranges, factoring seasonality and weather.
5. **Personalized recommendations** — a ranked, quantified action list ("Fix suspected bathroom leak → est. 12 OMR/mo", "Shift laundry off-peak → est. 4 OMR/mo").
6. **Tips & education** — contextual, localized efficiency tips tied to the user's actual profile.
7. **Alerts & notifications** — proactive push/email when an anomaly or probable leak is detected.

### 3.2 What makes it different
- **Personalized, not generic** — every insight is grounded in the user's own history and comparable peers.
- **Explains the *why*** — not just "usage is up 30%" but a probable cause and a recommended action.
- **Quantifies savings** — every recommendation carries an estimated OMR impact, so users act on the highest-value items first.
- **Works with what users already have** — bills, not mandatory hardware. Smart-meter integration is an enhancement, not a prerequisite.

---

## 4. Target Users & Personas

| Persona | Need | Primary value |
|---|---|---|
| **Cost-conscious homeowner** | "Why is my bill so high, and how do I lower it?" | Anomaly alerts + ranked savings actions |
| **Property manager / landlord** | Monitor multiple units, catch leaks fast | Multi-property dashboard, leak alerts |
| **Small business owner** | Control operating costs | Forecasting + tariff optimization |
| **Sustainability-minded user** | Reduce environmental footprint | Usage insights + efficiency tips |
| **(B2B, later) Utility / municipality** | Reduce non-revenue water, promote efficiency to customers | Aggregate analytics, white-label |

---

## 5. Key Features (Detailed)

### 5.1 Bill ingestion & data capture
- Upload PDF / photo of a bill → OCR extraction of period, consumption, tariff, charges.
- Manual entry fallback (guided form).
- Direct connection to utility accounts where supported (roadmap).
- Multi-utility support: water and electricity in one account; multiple properties per user.

### 5.2 Anomaly & pattern detection
- Per-user baseline modeling from historical bills.
- Seasonal decomposition to separate expected seasonal swings from true anomalies.
- Peer-cohort comparison (similar home size / occupancy / region) — privacy-preserving, aggregated.
- Severity scoring so users see the most important issues first.

### 5.3 Leak & inefficiency diagnosis
- Rule-based domain heuristics (e.g. sustained non-zero minimum flow suggests a leak; flat high baseline suggests standby/phantom load).
- ML classification to label anomaly type (leak vs. behavior change vs. appliance fault vs. tariff issue).
- Confidence indicator + suggested verification step ("check meter with all taps closed").

### 5.4 Forecasting
- Next-period consumption and cost prediction with confidence intervals.
- Weather/temperature-adjusted forecasts (cooling load is a major driver in the Gulf).
- "End-of-month projection" that updates as the period progresses (with smart-meter/interim data).

### 5.5 Personalized recommendations
- Ranked action list, each with: description, probable cause, **estimated savings (OMR)**, effort level, and category (behavioral / maintenance / upgrade / tariff).
- Recommendations adapt as the user acts and as new data arrives.

### 5.6 Tips & education
- Localized, seasonally relevant tips.
- Tied to the user's actual profile (no "insulate your loft" for a Gulf apartment).

### 5.7 Alerts & notifications
- Proactive anomaly and probable-leak alerts (email + push).
- Configurable thresholds and quiet hours.

### 5.8 Dashboard & reporting
- At-a-glance status: current spend, forecast, open recommendations, savings achieved.
- Historical trends (water and electricity), exportable reports.
- "Savings tracker" — cumulative OMR saved by acting on recommendations (drives retention).

---

## 6. AI / ML Approach

> Baseerah's intelligence combines **classical time-series/statistical methods** (transparent, data-efficient, work from month 1) with **machine-learning models** (higher accuracy as data accumulates) and an **LLM layer** (for natural-language explanations and localized tips).

### 6.1 Anomaly detection
- **Baseline & residual analysis:** seasonal-trend decomposition (e.g. STL), rolling statistics, and z-score/IQR-based outlier flagging on the residual.
- **ML detectors** as data grows: Isolation Forest / autoencoder-based reconstruction error for multivariate patterns.
- **Cold-start strategy:** for new users with little history, lean on peer-cohort norms and rule-based checks until a personal baseline forms.

### 6.2 Leak / inefficiency classification
- Feature engineering from consumption shape (minimum/baseline load, ramp patterns, day/night ratios where interval data exists).
- Supervised classifier once labeled data accrues; rule-based heuristics until then (heuristics remain as an explainable safety net).

### 6.3 Forecasting
- Baseline: seasonal-naive and exponential smoothing for immediate value.
- Upgraded: gradient-boosted regressors (e.g. XGBoost/LightGBM) or Prophet-style models incorporating weather, seasonality, and tariff calendar.
- Confidence intervals communicated clearly (never a false-precision single number).

### 6.4 Recommendation engine
- Maps detected issues → candidate actions from a curated, localized knowledge base.
- Quantifies each action's savings from the user's own consumption and tariff.
- Ranks by expected value (savings × likelihood) and effort.

### 6.5 LLM layer (explanations & tips)
- Uses the latest Claude models (e.g. Claude Opus / Sonnet 4.x) to translate model outputs into clear, empathetic, **Arabic + English** explanations and to generate contextual tips.
- **Guardrail:** the LLM *explains* and *phrases* — it does not invent the numbers. All figures come from the deterministic analytics layer, so recommendations are auditable and trustworthy.

### 6.6 Model quality & trust
- Human-readable "why we flagged this" for every alert.
- Feedback loop: users confirm/dismiss alerts → labels improve future models.
- Conservative defaults: better to under-alert than to erode trust with false alarms.

---

## 7. Data Requirements

| Data | Source | Purpose | Notes |
|---|---|---|---|
| Historical bills (period, consumption, cost, tariff) | User upload / utility API | Baseline, anomaly, forecast | Minimum viable; more history = better models |
| Property attributes (size, occupancy, type) | User onboarding | Cohort matching, personalization | Optional but valuable |
| Tariff structures | Utility publications | Accurate cost math & savings estimates | Maintained per-region |
| Weather / temperature | Public weather API | Cooling-load-adjusted forecasts | Regional |
| Smart-meter interval data (future) | Utility API / IoT | Higher-resolution detection | Enhancement, not required |
| User feedback on alerts | In-app | Model improvement | Closes the loop |

**Cold-start:** the system delivers value from the **first bill or two** via rules + cohort norms, and gets sharper as history accumulates.

---

## 8. User Experience & Flow

1. **Onboard** — sign up, add a property, enter/upload first bill(s), answer a few profile questions.
2. **First insight** — immediate baseline + any obvious flags + a first forecast.
3. **Ongoing** — each new bill (or smart-meter sync) refreshes analysis; user gets alerts and an updated recommendation list.
4. **Act & track** — user marks recommendations as done; savings tracker updates; models learn from feedback.

Design principles: mobile-first, bilingual (Arabic/English) with RTL support, minimal jargon, every insight one tap from "what do I do about it."

---

## 9. Technical Architecture

### 9.1 High-level

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│  Web client │────▶│   API layer  │────▶│  Analytics/ML svc  │
│ (React/Next)│     │ (REST/GraphQL)│     │ (Python: models,   │
└─────────────┘     └──────┬───────┘     │  forecasting,      │
                           │             │  anomaly, leak)    │
                    ┌──────▼───────┐     └─────────┬──────────┘
                    │  App/DB      │               │
                    │ (Postgres)   │◀──────────────┘
                    └──────┬───────┘
                           │
        ┌──────────────────┼───────────────────┐
        ▼                  ▼                    ▼
   ┌─────────┐      ┌─────────────┐      ┌─────────────┐
   │  OCR /  │      │  LLM API    │      │ Weather API │
   │ parsing │      │ (Claude)    │      │ / utilities │
   └─────────┘      └─────────────┘      └─────────────┘
```

### 9.2 Proposed stack (indicative — to be finalized in Phase 0)
- **Frontend:** React / Next.js, TypeScript, Tailwind; i18n (Arabic RTL + English); mobile-responsive.
- **Backend/API:** Node.js (TypeScript) or Python (FastAPI) — align with team strength.
- **Analytics/ML:** Python (pandas, scikit-learn, statsmodels/Prophet, XGBoost/LightGBM), served as an internal service or scheduled jobs.
- **LLM:** Claude API for explanations and tip generation.
- **OCR:** managed OCR service or open-source (Tesseract) with a bill-specific parsing layer.
- **Database:** PostgreSQL (relational bill/user data); object storage for uploaded bill files.
- **Infra:** cloud-hosted (region-appropriate for data residency), containerized, CI/CD.
- **Notifications:** email + web push (and mobile push later).

*(Final choices depend on team skills, data-residency requirements, and budget — locked in Phase 0.)*

---

## 10. Security, Privacy & Compliance

- **Sensitive data:** utility bills reveal occupancy patterns and personal financial info — treated as PII.
- **Encryption** in transit (TLS) and at rest for bill data and files.
- **Access control & auth** on all account/data endpoints; least-privilege.
- **Data minimization:** collect only what improves the product; peer comparisons use aggregated, anonymized cohorts — never expose one user's data to another.
- **User control:** export and delete-my-data functionality.
- **Data residency:** host in a region consistent with Omani/GCC data-protection expectations.
- **LLM boundary:** avoid sending unnecessary PII to third-party LLM APIs; send the minimum context needed, or use redaction.
- **Auditability:** every automated recommendation is explainable and traceable to source figures.

---

## 11. Business Model & Go-to-Market

### 11.1 Revenue options
- **Freemium (B2C):** free tier (basic analysis, limited history) → premium subscription (multi-property, forecasting, priority alerts, deeper diagnostics).
- **B2B / white-label:** utilities, municipalities, and property-management firms license the platform for their customers or portfolios.
- **ESG / enterprise:** organizations tracking sustainability KPIs.

### 11.2 Go-to-market
- Phase 1: direct B2C acquisition + a design-partner pilot (property manager or a cohort of households).
- Phase 2: institutional pilot with a utility/municipality.

### 11.3 Value proposition (crisp)
- **Users:** "Cut your water and electricity bills — Baseerah tells you exactly where you're losing money and what to fix first."
- **Institutions:** "Reduce non-revenue water and energy waste across your customer base with AI-driven consumption intelligence."

---

## 12. Roadmap & Phasing

### Phase 0 — Discovery & setup *(short)*
- Finalize stack, data model, tariff/weather data sources, and design-partner(s).
- Legal/privacy baseline; sample bill collection for parser development.

### Phase 1 — MVP
- Bill upload + OCR/parsing (or manual entry).
- Baseline + rule-based anomaly & leak detection.
- Simple forecast + cost projection.
- Basic recommendations + tips + dashboard.
- Bilingual UI, auth, core security.
- **Goal:** validated pilot; prove users act on insights and save money.

### Phase 2 — Intelligence deepening
- ML anomaly detection & leak classification (trained on accumulated + feedback data).
- Weather-adjusted forecasting with confidence intervals.
- LLM-generated explanations and localized tips.
- Alerts/notifications, savings tracker, multi-property.

### Phase 3 — Scale & integrations
- Direct utility-account / smart-meter integrations.
- B2B / white-label offering, aggregate analytics dashboard.
- Mobile app.

*(Timelines and resourcing to be attached once Phase 0 scoping is done.)*

---

## 13. Success Metrics

**Product/impact**
- Average % reduction in users' utility bills after 3 months.
- Total OMR / liters / kWh saved (aggregate) — the headline sustainability number.
- Leak/anomaly detection precision & recall (measured against user-confirmed feedback).
- Forecast accuracy (MAPE).

**Engagement/business**
- Activation (uploaded ≥1 bill and viewed first insight).
- Retention (monthly active; bills added per user).
- Recommendation action rate (% of recommendations marked done).
- Free→premium conversion; B2B pilots signed.

---

## 14. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Bill parsing accuracy** (varied formats) | Bad data → bad insights | Start with manual entry fallback; build robust per-utility parsers; validate extracted figures against expected ranges |
| **Cold start** (little history) | Weak early insights | Rules + peer cohorts from day 1; set expectations; improve with each bill |
| **False alarms** erode trust | Churn | Conservative thresholds, explainability, easy dismiss + feedback loop |
| **Utility API availability** | Limits smart-meter features | Design bill-first; treat integrations as enhancements |
| **Data privacy concerns** | Adoption barrier | Strong security posture, transparency, user data control, data residency |
| **LLM hallucination** in advice | Trust/liability | LLM never invents numbers; deterministic analytics own all figures; explanations are audited |
| **Tariff changes** | Wrong savings math | Centralized, maintained tariff config per region |

---

## 15. Team & Resourcing *(to be completed)*

Indicative roles: product/PM, full-stack engineer(s), a data/ML engineer, UX designer (bilingual/RTL), and a domain advisor (utility/energy). Exact allocation to be defined with the Phase 0 plan and budget.

---

## 16. Recommendation

Baseerah addresses a real, quantifiable pain (opaque bills, hidden leaks, no forward visibility) for a large audience, with strong regional tailwinds and a credible technical path that delivers value from the first bill while getting smarter over time. Its defensibility grows with data and the personalization/feedback loop.

**Proposed next step:** approve **Phase 0** — a short discovery sprint to lock the stack, secure a design partner, gather sample bills, and produce a costed Phase 1 MVP plan with timelines.

---

*Appendices (to be added): sample bill formats & parsing notes · tariff data sources · detailed data model · wireframes · competitive landscape.*
