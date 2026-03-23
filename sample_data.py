"""
Sample credit memo data for the SME Review Portal demo.
Borrower: Acme Industrial Corp — $75M credit facility.
"""

SAMPLE_MEMO = {
    "memo_id": "CM-2024-0847",
    "created_at": "2024-11-15T09:23:41Z",

    "borrower": {
        "name": "Acme Industrial Corp",
        "industry": "Industrial Manufacturing",
        "naics_code": "332999",
        "headquarters": "Columbus, OH",
        "years_in_business": 34,
        "employees": 2_847,
        "ownership": "Private Equity — Summit Capital Partners (87%), Mgmt (13%)",
    },

    "loan_request": {
        "amount": 75_000_000,
        "type": "Senior Secured Credit Facility",
        "term_loan_amount": 50_000_000,
        "revolver_amount": 25_000_000,
        "term": "5 years",
        "purpose": "Acquisition of Precision Parts LLC ($48M) and general working capital",
        "collateral": "First lien on all assets; pledge of 100% of subsidiary equity",
    },

    "ml_model_scores": {
        "model_version": "CreditScore-v2.4.1",
        "model_decision": "APPROVE",
        "model_confidence": 0.81,
        "probability_of_default": 0.0387,
        "loss_given_default": 0.342,
        "expected_loss": 0.01324,
        "risk_grade": "B+",
        "pd_threshold": 0.06,
        "lgd_threshold": 0.50,
        "el_threshold": 0.03,
    },

    "sections": [
        {
            "id": "executive_summary",
            "icon": "📋",
            "title": "Executive Summary",
            "sources": ["10-K FY2023", "Management Presentation Q3 2024", "CIM Oct 2024"],
            "generated_text": (
                "Acme Industrial Corp ('Acme' or 'the Company') is requesting a $75 million senior secured "
                "credit facility comprising a $50 million term loan and a $25 million revolving credit facility "
                "to fund the acquisition of Precision Parts LLC and support working capital needs.\n\n"
                "Acme is a 34-year-old Ohio-based industrial manufacturer serving the automotive, aerospace, and "
                "heavy equipment sectors. The Company generated $371.2 million in revenue and $58.9 million in "
                "EBITDA (15.9% margin) for FY2023, representing 8.3% and 12.1% YoY growth respectively.\n\n"
                "The ML risk model scores Acme at B+ with a probability of default of 3.87%, well inside the "
                "6.0% policy threshold. Pro forma leverage of 4.5x EBITDA is elevated but manageable given "
                "the Company's strong free cash flow conversion (72%) and the strategic rationale of the "
                "Precision Parts acquisition, which is expected to add $28M in revenue and $5.2M in EBITDA "
                "in year one.\n\n"
                "Recommendation: APPROVE subject to standard covenants and the conditions outlined in the "
                "Recommendation section."
            ),
        },
        {
            "id": "borrower_overview",
            "icon": "🏢",
            "title": "Borrower Overview",
            "sources": ["10-K FY2023", "Management Presentation Q3 2024", "D&B Report Nov 2024"],
            "generated_text": (
                "Acme Industrial Corp was founded in 1990 and is headquartered in Columbus, Ohio. The Company "
                "designs and manufactures precision metal components and sub-assemblies for OEM customers across "
                "three end markets: automotive (51% of revenue), aerospace & defense (31%), and heavy equipment "
                "(18%).\n\n"
                "With 2,847 employees across five manufacturing facilities (OH, MI, TN, TX, and a recently "
                "acquired plant in Monterrey, Mexico), Acme operates a vertically integrated production model "
                "covering stamping, machining, welding, and surface treatment.\n\n"
                "Ownership structure: Summit Capital Partners acquired a majority stake in 2019 for $210M "
                "(implied 6.8x EBITDA at the time). Management retains 13% equity. Summit's investment thesis "
                "centers on roll-up consolidation in fragmented precision parts manufacturing — Precision Parts "
                "LLC would be the fourth add-on acquisition under Summit's ownership.\n\n"
                "Key customers include Ford Motor (18% of revenue), Lockheed Martin (14%), and Caterpillar (9%). "
                "The top 5 customers account for 52% of revenue, representing moderate concentration risk. All "
                "top-5 relationships have multi-year supply agreements in place through at least 2026."
            ),
        },
        {
            "id": "financial_analysis",
            "icon": "📊",
            "title": "Financial Analysis",
            "sources": ["Audited Financials FY2021-FY2023", "Management Accounts Q3 2024", "Model Output"],
            "generated_text": (
                "Revenue has grown at a 3-year CAGR of 7.1%, from $302.4M (FY2021) to $371.2M (FY2023). "
                "Growth is driven by increased automotive content-per-vehicle, new aerospace program wins, "
                "and the 2022 acquisition of MidWest Stampings.\n\n"
                "EBITDA has expanded from $43.8M (14.5% margin, FY2021) to $58.9M (15.9% margin, FY2023), "
                "reflecting operating leverage and manufacturing efficiency gains. TTM EBITDA through Q3 2024 "
                "is $61.4M, implying annualized margin improvement to 16.2%.\n\n"
                "Key credit metrics (pro forma for the acquisition):\n"
                "  • Total Debt / EBITDA: 4.5x (vs. 3.1x pre-acquisition)\n"
                "  • Interest Coverage (EBIT/Interest): 3.2x\n"
                "  • Fixed Charge Coverage Ratio: 1.4x\n"
                "  • Free Cash Flow Conversion: 72% of EBITDA\n"
                "  • CapEx / Revenue: 4.1% (maintenance 2.2%, growth 1.9%)\n\n"
                "Liquidity: Pro forma cash of $12.3M plus full $25M revolver availability provides adequate "
                "liquidity. The Company has no near-term debt maturities prior to this facility.\n\n"
                "Note: The model used TTM EBITDA of $61.4M for the PD calculation. The audited FY2023 figure "
                "of $58.9M would produce a slightly higher PD of 4.12%, still within policy threshold."
            ),
        },
        {
            "id": "risk_factors",
            "icon": "⚠️",
            "title": "Risk Factors",
            "sources": ["Industry Reports", "10-K FY2023 Risk Factors", "Management Discussion"],
            "generated_text": (
                "1. Customer Concentration — Ford Motor accounts for 18% of revenue. A significant reduction "
                "in Ford's production volumes (e.g., EV transition disruption, UAW strike impact) would "
                "materially affect Acme's top line. Mitigant: Ford relationship is contractual through 2027; "
                "Acme supplies platform-agnostic components used in both ICE and EV models.\n\n"
                "2. EV Transition Risk — Approximately 30% of automotive revenue is tied to traditional "
                "powertrain components (engine mounts, transmission housings) that face long-term secular "
                "decline as EV adoption accelerates. Management projects this content to represent only 18% "
                "of auto revenue by 2028 through new EV platform wins. This transition timeline should be "
                "stress-tested.\n\n"
                "3. Acquisition Integration Risk — Precision Parts LLC operates on legacy ERP systems and "
                "has a different manufacturing culture. The three prior Summit add-ons averaged 14 months to "
                "full integration. A prolonged integration could delay the projected $5.2M EBITDA contribution.\n\n"
                "4. Raw Material Exposure — Steel and aluminum represent 38% of COGS. The Company has "
                "cost-pass-through clauses with 71% of customers (by revenue), leaving 29% exposed to "
                "commodity volatility. No active hedging program is in place.\n\n"
                "5. Leverage — Pro forma net leverage of 4.5x is above the 4.0x peer median for B+ rated "
                "industrial manufacturers. Deleveraging to below 4.0x within 24 months is achievable but "
                "requires the Precision Parts synergies to materialize on schedule."
            ),
        },
        {
            "id": "covenants_structure",
            "icon": "📝",
            "title": "Covenants & Structure",
            "sources": ["Term Sheet Draft v3", "Legal Counsel Review", "Credit Policy Manual"],
            "generated_text": (
                "Proposed financial covenants (tested quarterly):\n"
                "  • Maximum Total Net Leverage: 5.0x (stepping down to 4.5x at month 18, 4.0x at month 30)\n"
                "  • Minimum Fixed Charge Coverage Ratio: 1.20x\n"
                "  • Maximum Annual CapEx: $18M (with carryforward provision of up to $3M)\n\n"
                "Security package:\n"
                "  • First priority lien on all present and after-acquired assets of the borrower and "
                "    guarantors (accounts receivable, inventory, equipment, IP, real property)\n"
                "  • Pledge of 100% of equity interests in all domestic subsidiaries\n"
                "  • Pledge of 65% of equity in foreign subsidiaries (Monterrey entity)\n\n"
                "Mandatory prepayments:\n"
                "  • 50% excess cash flow sweep (if leverage > 3.5x; 25% if 3.0x–3.5x; 0% if < 3.0x)\n"
                "  • 100% of net proceeds from asset disposals > $5M\n"
                "  • 100% of net proceeds from additional debt issuances\n\n"
                "Negative covenants include restrictions on additional indebtedness (carve-out: $10M basket), "
                "restricted payments (no dividends while leverage > 3.5x), and material asset disposals "
                "without lender consent.\n\n"
                "The leverage step-down schedule is aggressive relative to comparable transactions (B+ rated "
                "industrial, PE-sponsored). Consider negotiating a 6-month cushion on the month-18 step-down "
                "to account for integration timing risk."
            ),
        },
        {
            "id": "recommendation",
            "icon": "✅",
            "title": "Recommendation",
            "sources": ["Credit Committee Guidelines", "Model Output", "Peer Benchmarking"],
            "generated_text": (
                "RECOMMENDATION: APPROVE\n\n"
                "The ML risk model scores Acme Industrial Corp at B+ with a PD of 3.87% and an expected loss "
                "of 1.32%, both comfortably within policy thresholds. The credit is supported by:\n\n"
                "  • Established 34-year operating history with diversified end-market exposure\n"
                "  • Consistent revenue and EBITDA growth (7.1% and 12.1% CAGRs respectively)\n"
                "  • Strong free cash flow conversion supporting deleveraging\n"
                "  • Experienced PE sponsor with a demonstrated acquisition playbook\n"
                "  • Robust security package with first-lien position on all assets\n\n"
                "Conditions precedent to funding:\n"
                "1. Completion of legal due diligence on Precision Parts LLC (target: Nov 30, 2024)\n"
                "2. Receipt of audited financials for Precision Parts LLC (FY2021–FY2023)\n"
                "3. Environmental Phase I assessment for the Monterrey facility\n"
                "4. Confirmation that no material adverse change has occurred since Q3 2024 management accounts\n"
                "5. Execution of intercreditor agreement with existing mezzanine lender\n\n"
                "The primary credit risk is EV transition exposure in the automotive segment. It is recommended "
                "that the credit officer request a sensitivity analysis showing EBITDA impact under a scenario "
                "where ICE-related revenue declines 25% by 2027, and confirm that covenant headroom is "
                "maintained under that stress."
            ),
        },
    ],
}
