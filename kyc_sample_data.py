"""
KYC Risk Investigator — Sample Alert Cases
Two realistic KYC scenarios: high-risk corporate + medium-risk individual.
"""

KYC_CASES = [
    {
        "case_id": "KYC-2024-0847",
        "alert_type": "New Client Onboarding",
        "alert_date": "2024-11-14",
        "priority": "HIGH",
        "client_type": "Corporate",
        "status": "Pending Review",
        "risk_score": 78,
        "risk_tier": "HIGH",

        "profile": {
            "entity_name": "TechBridge Global Ltd",
            "registration_country": "British Virgin Islands",
            "registration_number": "BVI-2023-441872",
            "incorporation_date": "2023-02-14",
            "business_type": "Technology Services / Investment Holdings",
            "industry": "Information Technology",
            "annual_revenue_declared": "$4.2M",
            "employees_declared": 12,
            "headquarters": "Road Town, Tortola, BVI",
            "operating_address": "Dubai, UAE",
            "beneficial_owner": "Viktor Sorokin",
            "ownership_layers": 3,
            "account_purpose": "Trade finance and payment processing",
            "relationship_manager": "James Chen",
        },

        "risk_factors": [
            {
                "factor": "Sanctions Proximity",
                "score": 85, "tier": "HIGH",
                "detail": "Beneficial owner name/DOB near-match to OFAC SDN-listed individual (1-day DOB delta)",
            },
            {
                "factor": "Geographic Risk",
                "score": 80, "tier": "HIGH",
                "detail": "BVI incorporation + UAE operations — both FATF-monitored jurisdictions",
            },
            {
                "factor": "Ownership Opacity",
                "score": 90, "tier": "HIGH",
                "detail": "3-layer holding structure; Layer 2-3 UBO not fully disclosed",
            },
            {
                "factor": "PEP Connection",
                "score": 65, "tier": "MEDIUM",
                "detail": "Business partner connected to Russian state energy sector",
            },
            {
                "factor": "Transaction Velocity",
                "score": 55, "tier": "MEDIUM",
                "detail": "3 large round-number transfers in first 30 days — atypical for new client",
            },
            {
                "factor": "Document Completeness",
                "score": 40, "tier": "MEDIUM",
                "detail": "Passport provided; corporate docs incomplete; no utility bill",
            },
        ],

        "ml_scores": {
            "composite_risk_score": 78,
            "sanctions_match_probability": 0.67,
            "pep_connection_probability": 0.43,
            "aml_flag_probability": 0.58,
            "model_version": "kyc-risk-v2.1",
            "model_recommendation": "ESCALATE",
            "model_confidence": 0.74,
        },

        "documents": [
            {
                "doc_type": "Passport",
                "holder": "Viktor Sorokin",
                "nationality": "Russian Federation",
                "dob": "1971-08-22",
                "expiry_date": "2030-03-09",
                "status": "Extracted",
                "flags": [
                    "Near-match to SDN entry: Viktor Sorokin (DOB: 1971-08-23, 1-day delta)",
                ],
            },
            {
                "doc_type": "Certificate of Incorporation",
                "entity": "TechBridge Global Ltd",
                "jurisdiction": "British Virgin Islands",
                "date": "2023-02-14",
                "status": "Extracted",
                "flags": [
                    "Registered agent linked to 47 other entities under AML review",
                ],
            },
            {
                "doc_type": "Beneficial Ownership Declaration",
                "status": "Incomplete",
                "flags": [
                    "Layer 2 holding company (Cyprus HoldCo) not disclosed",
                    "No UBO confirmation beyond Layer 1",
                ],
            },
        ],

        "intelligence": {
            "news_items": [
                {
                    "source": "Reuters",
                    "date": "2023-11-08",
                    "headline": "BVI shell companies linked to Russian oligarch network under US scrutiny",
                    "relevance": "HIGH",
                    "snippet": "A network of BVI-registered technology holding companies directed funds through Dubai intermediaries…",
                },
                {
                    "source": "OCCRP",
                    "date": "2024-01-22",
                    "headline": "Viktor Sorokin named in leaked financial documents",
                    "relevance": "HIGH",
                    "snippet": "Documents show Sorokin directing payments through UAE-based intermediaries into Western financial systems.",
                },
                {
                    "source": "Dubai Business Register",
                    "date": "2023-06-15",
                    "headline": "TechBridge Global registered as UAE branch office",
                    "relevance": "MEDIUM",
                    "snippet": "Single director; operations described as 'technology consulting'. No public clients identified.",
                },
            ],
            "transaction_patterns": {
                "expected_monthly_volume": "$350K",
                "counterparty_countries": ["UAE", "Cyprus", "Cayman Islands", "Singapore"],
                "funding_source": "Wire transfers from undisclosed BVI entity",
                "velocity_flag": True,
                "velocity_detail": "3 round-number wire transfers ($500K, $750K, $500K) within 30 days of onboarding",
            },
        },

        "ai_narrative": (
            "**KYC Risk Assessment — TechBridge Global Ltd**\n\n"
            "This case presents a **high-risk profile** requiring Enhanced Due Diligence (EDD) "
            "before account activation. Three independent risk signals converge:\n\n"
            "**1. Sanctions Proximity (Critical)**  \n"
            "Beneficial owner Viktor Sorokin (DOB: 1971-08-22) is a near-exact match to OFAC SDN "
            "entry Viktor Sorokin (DOB: 1971-08-23). A 1-day DOB delta is a known obfuscation "
            "technique. Passport verification alone is insufficient — independent identity "
            "confirmation and sanctions screening team sign-off are required.\n\n"
            "**2. Ownership Structure (High)**  \n"
            "The 3-layer BVI → Cyprus → Unknown holding structure is a classic sanctions-evasion "
            "architecture. FATF Recommendation 10 requires disclosure of the ultimate beneficial "
            "owner. Layer 2–3 remain undisclosed. This is a hard compliance blocker.\n\n"
            "**3. Intelligence Alignment (High)**  \n"
            "OCCRP investigative reporting directly references 'Viktor Sorokin directing payments "
            "through UAE intermediaries' — language that mirrors this client's operating setup. "
            "The shared registered agent (linked to 47 other flagged entities) further elevates "
            "the structural risk.\n\n"
            "**Recommendation: ESCALATE** — Do not activate. Refer to Level 2 compliance with "
            "sanctions team review. Require full UBO chain disclosure and source-of-funds "
            "documentation from an independent correspondent bank."
        ),
    },
    {
        "case_id": "KYC-2024-0851",
        "alert_type": "Ongoing Monitoring — Behavioral Alert",
        "alert_date": "2024-11-16",
        "priority": "MEDIUM",
        "client_type": "Individual",
        "status": "Pending Review",
        "risk_score": 52,
        "risk_tier": "MEDIUM",

        "profile": {
            "entity_name": "Ahmad Karimov",
            "registration_country": "Kazakhstan",
            "nationality": "Kazakh",
            "dob": "1984-03-11",
            "occupation": "Private Equity Analyst",
            "employer": "Self-employed / Karimov Capital LLC",
            "annual_income_declared": "$180K",
            "address": "Frankfurt, Germany (resident since 2019)",
            "account_purpose": "Investment and personal banking",
            "relationship_manager": "Sarah Mueller",
            "customer_since": "2020-03-01",
        },

        "risk_factors": [
            {
                "factor": "PEP Connection",
                "score": 70, "tier": "HIGH",
                "detail": "Uncle is Deputy Minister of Finance, Kazakhstan (active PEP)",
            },
            {
                "factor": "Geographic Risk",
                "score": 60, "tier": "MEDIUM",
                "detail": "Kazakhstan is FATF grey-listed; frequent transfers to/from Almaty",
            },
            {
                "factor": "Income Inconsistency",
                "score": 65, "tier": "MEDIUM",
                "detail": "Cash deposits of €340K in 6 months vs €180K declared annual income",
            },
            {
                "factor": "Device / IP Changes",
                "score": 50, "tier": "MEDIUM",
                "detail": "7 new device registrations in 60 days — unusually high for retail client",
            },
            {
                "factor": "Transaction Velocity",
                "score": 45, "tier": "LOW",
                "detail": "Outbound transfers spiked 3× vs 12-month baseline in October 2024",
            },
            {
                "factor": "Document Completeness",
                "score": 20, "tier": "LOW",
                "detail": "Full KYC pack on file; last refreshed 18 months ago",
            },
        ],

        "ml_scores": {
            "composite_risk_score": 52,
            "sanctions_match_probability": 0.04,
            "pep_connection_probability": 0.81,
            "aml_flag_probability": 0.39,
            "model_version": "kyc-risk-v2.1",
            "model_recommendation": "ENHANCED_DD",
            "model_confidence": 0.68,
        },

        "documents": [
            {
                "doc_type": "Passport (German Residence Permit)",
                "holder": "Ahmad Karimov",
                "nationality": "Kazakhstan",
                "expiry_date": "2027-03-10",
                "status": "Extracted",
                "flags": [],
            },
            {
                "doc_type": "Source of Funds Declaration",
                "status": "Extracted",
                "flags": [
                    "Declared source: 'Investment returns from Kazakhstan real estate'",
                    "No supporting documentation for real estate holdings provided",
                ],
            },
            {
                "doc_type": "Tax Return (Germany, 2023)",
                "status": "Extracted",
                "flags": [
                    "Declared income: €162K — gap vs €340K cash deposits",
                ],
            },
        ],

        "intelligence": {
            "news_items": [
                {
                    "source": "Kazakh Ministry of Finance",
                    "date": "2024-09-01",
                    "headline": "Deputy Minister Bakyt Karimov re-appointed to Finance portfolio",
                    "relevance": "HIGH",
                    "snippet": "Client's uncle holds senior government finance role with discretionary budget authority.",
                },
                {
                    "source": "Transparency International",
                    "date": "2023-06-30",
                    "headline": "Kazakhstan: CPI score 35/100 — persistent corruption risk",
                    "relevance": "MEDIUM",
                    "snippet": "Central Asian nations with government-linked wealth remain elevated financial crime risk.",
                },
            ],
            "transaction_patterns": {
                "expected_monthly_volume": "$15K",
                "counterparty_countries": ["Kazakhstan", "UAE", "Germany"],
                "funding_source": "Mixed: salary credits + large periodic cash deposits",
                "velocity_flag": True,
                "velocity_detail": "October 2024: €215K inflows vs €60K monthly average — 3.6× spike",
            },
        },

        "ai_narrative": (
            "**KYC Risk Assessment — Ahmad Karimov**\n\n"
            "This ongoing monitoring alert reflects a **medium-risk profile** driven primarily by "
            "PEP proximity and income inconsistency. No sanctions match; the core concern is "
            "potential misuse of a PEP relative's position.\n\n"
            "**1. PEP Exposure (High)**  \n"
            "The client's uncle, Bakyt Karimov, is an active Deputy Minister of Finance in "
            "Kazakhstan — a jurisdiction with a Transparency International CPI score of 35/100. "
            "PEP connections do not imply wrongdoing, but they require documented rationale for "
            "the banking relationship and ongoing monitoring of fund flows consistent with "
            "declared income.\n\n"
            "**2. Income vs. Deposit Gap (Medium)**  \n"
            "€340K in cash deposits over 6 months against €162K annual tax-declared income "
            "represents a ~2.1× discrepancy. The declared source ('Kazakhstan real estate returns') "
            "is unsupported by documentation. This gap requires a source-of-funds refresh.\n\n"
            "**3. Behavioral Anomaly (Medium)**  \n"
            "The October 2024 inflow spike (3.6× vs baseline) coincides with the uncle's "
            "reappointment to the Finance Ministry. While circumstantial, the timing warrants "
            "attention. 7 device changes in 60 days may indicate account sharing or operational "
            "security measures.\n\n"
            "**Recommendation: ENHANCED DUE DILIGENCE** — Refresh KYC pack, obtain "
            "source-of-funds documentation for real estate holdings, and document the PEP "
            "rationale. Re-score after refresh. No account restriction required at this stage."
        ),
    },
]
