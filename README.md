# Sales Operations Dashboard — Illustrative SaaS Analytics

A portfolio project demonstrating Sales Operations and Revenue Operations
analytical capabilities across a simulated three-product SaaS environment,
built in both Power BI and Tableau.

---

## Overview

This project simulates a Sales Operations dashboard for a financial SaaS
company with three distinct product lines:

- **ActiveDisclosure** — recurring SaaS, SEC reporting compliance
- **Venue** — event-driven, M&A/IPO virtual data rooms
- **Arc Suite** — recurring SaaS, fund/investment company compliance

The dataset was purpose-built to reflect realistic product-level dynamics:
different sales cycle lengths, win rates, seasonality patterns, and
churn profiles for each product line.

---

## Dashboard Pages

### Page 1 — Executive Summary
KPI cards: Total Bookings, NRR %, Win Rate, Stalled Deals, Open Pipeline
Monthly bookings trend by division | Quarterly bookings by division

### Page 2 — Pipeline Health & Deal Risk
Open pipeline by stage | Stalled deals action table
Loss reason breakdown | Competitive loss analysis

### Page 3 — Forecast & Acquisition Economics
Forecast vs. actual bookings by quarter | Forecast variance % by division
CAC Payback Period by division | LTV:CAC Ratio by division

### Page 4 — Cross-Division Efficiency
Cross-division vs. single-division win rate comparison
White space analysis by account segment
Cross-division won deal trend | Expansion target account list

---

## Skills Demonstrated

**Data Modeling**
- Star schema design: fact tables (opportunities, quota, marketing spend)
  joined to dimension tables (accounts, reps, date)
- Separate pre-aggregated summary tables for SaaS metrics
  (NRR, CAC, ARR) with quarter_dim bridge table
- Relationship management: active/inactive relationships,
  cross-filter direction, ambiguous path resolution

**DAX (Power BI)**
- CALCULATE with boolean filters (is_won, is_closed)
- VAR/RETURN pattern for multi-step measures
- DIVIDE for safe division with zero-denominator handling
- LASTDATE for point-in-time ARR snapshots
- AVERAGEX for context-aware rep attainment calculations
- DISTINCTCOUNT for account-level product penetration

**SaaS Metrics**
- ARR, MRR, ARPU (recurring products only)
- NRR and GRR with ARR waterfall events
  (New / Expansion / Contraction / Churn / Renewal)
- CAC calculated on trailing-12-month basis
- LTV using ARPU x Gross Margin / Churn Rate
- LTV:CAC ratio and CAC Payback Period by product line
- Forecast accuracy: committed vs. actual variance %

**Sales Operations Analytics**
- Pipeline coverage ratio and stage distribution
- Stalled deal identification using stage/time thresholds
- Win rate by division, stage conversion analysis
- Competitive loss analysis by competitor
- Cross-division deal win rate vs. single-division baseline
- Account white space analysis for expansion targeting

**Python (Data Generation)**
- Synthetic dataset generation using pandas, numpy, faker
- Realistic seasonality modeling by product line
- Subscription state simulation with monthly churn events
- Trailing-12-month CAC calculation methodology
- Power Query M language for cross-table aggregation

**Tableau**
- Multi-source data relationships
- Calculated fields for win rate and conversion metrics
- Reference lines for benchmark comparisons
- Dashboard assembly with cross-sheet filter actions
- Published to Tableau Public for portfolio access

---

## Dataset

Six CSV files simulating a CRM and billing system export:

| File | Description |
|---|---|
| opportunities.csv | 2,266 deals across 3 divisions, 2 years |
| accounts.csv | 480 accounts with segment and region |
| reps.csv | 21 reps with quota assignments |
| subscriptions.csv | Monthly subscription state for recurring products |
| marketing_spend.csv | Monthly S&M spend by channel and division |
| cac_summary.csv | Quarterly CAC, LTV, payback by division (T12M) |
| nrr_summary.csv | Quarterly ARR waterfall and NRR/GRR by division |
| arpu_arr_monthly.csv | Monthly ARR and ARPU trend |
| forecast_accuracy.csv | Quarterly forecast vs. actual by division |
| quota_attainment.csv | Monthly quota attainment by rep |

---

## Tools Used

- **Power BI Desktop** — primary dashboard
- **Tableau Public** — secondary dashboard
- **Python** (pandas, numpy, faker, dateutil) — data generation
- **DAX** — all measures and KPI calculations
- **Power Query (M)** — cross-table aggregation for white space analysis

---

## Note on Data

All data is synthetic and generated for portfolio purposes only.
No real company data is represented. Product names referenced
(ActiveDisclosure, Venue, Arc Suite) are used as illustrative
framework only to demonstrate domain knowledge of financial SaaS
go-to-market structures.

---

*Don Holbrook — Sales Operations & Revenue Operations Professional*
*Austin, TX | linkedin.com/in/donholbrook*
