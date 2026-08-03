"""
DFIN Sales Operations Dashboard — Data Generator
generate_data.py

Generates a CRM-style synthetic dataset across 3 product lines:
  - ActiveDisclosure (recurring SaaS, SEC reporting compliance)
  - Venue (event-driven, M&A/IPO virtual data rooms)
  - Arc Suite (recurring SaaS, fund/investment company compliance)

Output files:
  opportunities.csv, accounts.csv, reps.csv,
  quota_attainment.csv, forecast_accuracy.csv, date_dim.csv

Usage: python generate_data.py
Requirements: pip install pandas numpy faker python-dateutil
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ── Configuration ────────────────────────────────────────────────────────
PRODUCTS = {
    "ActiveDisclosure": {
        "type": "Recurring",
        "buyer": "Public Company Finance/IR",
        "avg_deal": 65000,
        "deal_std": 25000,
        "sales_cycle_days": 75,
        "win_rate": 0.32,
        "renewal_rate": 0.91,
        "seasonality_peak": [1, 2, 3, 10, 11],
    },
    "Venue": {
        "type": "Event-Driven",
        "buyer": "Investment Bank / PE / Corp Dev",
        "avg_deal": 42000,
        "deal_std": 30000,
        "sales_cycle_days": 35,
        "win_rate": 0.41,
        "renewal_rate": 0.55,
        "seasonality_peak": [1, 2, 5, 6, 9, 10],
    },
    "Arc Suite": {
        "type": "Recurring",
        "buyer": "Fund/Investment Company Compliance",
        "avg_deal": 58000,
        "deal_std": 20000,
        "sales_cycle_days": 90,
        "win_rate": 0.29,
        "renewal_rate": 0.93,
        "seasonality_peak": [2, 3, 4, 11],
    },
}

REGIONS = ["Northeast", "Mid-Atlantic", "Midwest", "Southeast", "West", "Texas/Central"]
REPS_PER_PRODUCT = 6
STAGES = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
STAGE_PROBABILITY = {
    "Prospecting": 10, "Qualification": 25, "Needs Analysis": 40,
    "Proposal": 60, "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0
}
LOSS_REASONS = ["Price", "Lost to Competitor", "No Decision / Stalled", "Budget Cut", "Timing - Not Ready", "Feature Gap"]
COMPETITORS = ["Workiva", "Intralinks", "Datasite", "Donnelley Legacy/Manual Process", "In-house Build", "Toppan Merrill", "Ideagen/Q4"]

TODAY      = datetime(2026, 6, 30)
DATA_START = TODAY - timedelta(days=730)

# ── 1. Reps ──────────────────────────────────────────────────────────────
reps = []
rep_id = 1000
for product in PRODUCTS:
    for i in range(REPS_PER_PRODUCT):
        reps.append({
            "rep_id":       rep_id,
            "rep_name":     fake.name(),
            "division":     product,
            "region":       random.choice(REGIONS),
            "hire_date":    fake.date_between(start_date="-5y", end_date="-90d"),
            "manager":      "Director, " + product + " Sales",
            "annual_quota": int(np.random.normal(PRODUCTS[product]["avg_deal"] * 14, 150000)),
        })
        rep_id += 1

# Overlay reps (cross-division)
for _ in range(3):
    reps.append({
        "rep_id":       rep_id,
        "rep_name":     fake.name(),
        "division":     "Cross-Division Overlay",
        "region":       random.choice(REGIONS),
        "hire_date":    fake.date_between(start_date="-3y", end_date="-180d"),
        "manager":      "VP, Strategic Accounts",
        "annual_quota": 1100000,
    })
    rep_id += 1

df_reps = pd.DataFrame(reps)

# ── 2. Accounts ───────────────────────────────────────────────────────────
N_ACCOUNTS = 480
account_segments = ["Large Cap Public", "Mid Cap Public", "Pre-IPO / Private",
                    "Investment Bank", "Private Equity", "Fund/Asset Manager"]

accounts = []
for i in range(N_ACCOUNTS):
    segment = random.choice(account_segments)
    if segment in ["Large Cap Public", "Mid Cap Public", "Pre-IPO / Private"]:
        natural_products = ["ActiveDisclosure", "Venue"]
    elif segment in ["Investment Bank", "Private Equity"]:
        natural_products = ["Venue"]
    else:
        natural_products = ["Arc Suite"]

    accounts.append({
        "account_id":       5000 + i,
        "account_name":     fake.company(),
        "segment":          segment,
        "region":           random.choice(REGIONS),
        "natural_products": natural_products,
        "employee_count":   random.choice([50, 150, 400, 800, 1500, 3000, 8000]),
    })

df_accounts = pd.DataFrame(accounts)

# ── 3. Opportunities ──────────────────────────────────────────────────────
def random_date_with_seasonality(product_cfg, start, end):
    days_range = (end - start).days
    for _ in range(10):
        d = start + timedelta(days=random.randint(0, days_range))
        if d.month in product_cfg["seasonality_peak"] or random.random() < 0.35:
            return d
    return start + timedelta(days=random.randint(0, days_range))

opps   = []
opp_id = 100000

for product, cfg in PRODUCTS.items():
    product_reps  = df_reps[df_reps["division"] == product]["rep_id"].tolist()
    overlay_reps  = df_reps[df_reps["division"] == "Cross-Division Overlay"]["rep_id"].tolist()
    eligible_accts = df_accounts[df_accounts["natural_products"].apply(lambda x: product in x)]

    n_opps = int(950 * (75 / cfg["sales_cycle_days"]) * 0.6)

    for _ in range(n_opps):
        acct    = eligible_accts.sample(1).iloc[0]
        created = random_date_with_seasonality(cfg, DATA_START, TODAY - timedelta(days=5))

        is_cross_div   = random.random() < 0.12 and len(acct["natural_products"]) > 1
        rep_id_assigned = random.choice(overlay_reps) if is_cross_div else random.choice(product_reps)

        cycle_days  = max(10, int(np.random.normal(cfg["sales_cycle_days"], cfg["sales_cycle_days"] * 0.35)))
        deal_amount = max(8000, np.random.normal(cfg["avg_deal"], cfg["deal_std"]))

        days_since_created = (TODAY - created).days
        is_closed = days_since_created > cycle_days or random.random() < 0.15

        if is_closed:
            adj_win_rate = cfg["win_rate"] + (0.07 if is_cross_div else 0)
            won          = random.random() < adj_win_rate
            stage        = "Closed Won" if won else "Closed Lost"
            close_date   = created + timedelta(days=min(cycle_days, days_since_created))
            if close_date > TODAY:
                close_date = TODAY
            loss_reason = None if won else random.choice(LOSS_REASONS)
            competitor  = None if won else random.choice(COMPETITORS)
            probability = 100 if won else 0
        else:
            progress = min(0.95, days_since_created / cycle_days)
            if progress < 0.2:   stage = "Prospecting"
            elif progress < 0.4: stage = "Qualification"
            elif progress < 0.6: stage = "Needs Analysis"
            elif progress < 0.8: stage = "Proposal"
            else:                stage = "Negotiation"
            close_date  = created + timedelta(days=cycle_days)
            loss_reason = None
            competitor  = None
            probability = STAGE_PROBABILITY[stage]
            won         = None

        # Stalled flag
        days_in_stage = random.randint(1, max(2, cycle_days // 3))
        if not is_closed:
            if days_since_created > cfg["sales_cycle_days"] and stage in ["Prospecting","Qualification","Needs Analysis"]:
                is_stalled = random.random() < 0.55
            elif days_since_created > cfg["sales_cycle_days"] * 0.75 and stage in ["Proposal","Negotiation"]:
                is_stalled = random.random() < 0.30
            else:
                is_stalled = False
        else:
            is_stalled = False

        opps.append({
            "opp_id":                   opp_id,
            "account_id":               acct["account_id"],
            "account_name":             acct["account_name"],
            "segment":                  acct["segment"],
            "division":                 product,
            "rep_id":                   rep_id_assigned,
            "is_cross_division_deal":   is_cross_div,
            "region":                   acct["region"],
            "created_date":             created,
            "close_date":               close_date,
            "stage":                    stage,
            "probability":              probability,
            "amount":                   round(deal_amount, 2),
            "is_closed":                is_closed,
            "is_won":                   won,
            "is_renewal":               random.random() < 0.4 if cfg["type"] == "Recurring" else False,
            "loss_reason":              loss_reason,
            "competitor":               competitor,
            "is_stalled":               is_stalled,
            "sales_cycle_days_actual":  (close_date - created).days if is_closed else None,
            "fiscal_quarter":           f"FY{close_date.year}-Q{(close_date.month-1)//3+1}",
        })
        opp_id += 1

df_opps = pd.DataFrame(opps)

# ── 4. Quota Attainment ───────────────────────────────────────────────────
quota_rows = []
months = pd.date_range(start=DATA_START, end=TODAY, freq="MS")

for _, rep in df_reps.iterrows():
    monthly_quota = rep["annual_quota"] / 12
    for month in months:
        month_end  = month + pd.offsets.MonthEnd(0)
        won_in_month = df_opps[
            (df_opps["rep_id"] == rep["rep_id"]) &
            (df_opps["is_won"] == True) &
            (df_opps["close_date"] >= month) &
            (df_opps["close_date"] <= month_end)
        ]
        bookings = won_in_month["amount"].sum()
        quota_rows.append({
            "rep_id":         rep["rep_id"],
            "rep_name":       rep["rep_name"],
            "division":       rep["division"],
            "month":          month,
            "monthly_quota":  round(monthly_quota, 2),
            "bookings":       round(bookings, 2),
            "attainment_pct": round((bookings / monthly_quota) * 100, 1) if monthly_quota > 0 else 0,
        })

df_quota = pd.DataFrame(quota_rows)

# ── 5. Forecast Accuracy ──────────────────────────────────────────────────
forecast_rows = []
quarters = sorted(df_opps["fiscal_quarter"].dropna().unique())

for q in quarters:
    for division in PRODUCTS.keys():
        actual = df_opps[
            (df_opps["fiscal_quarter"] == q) &
            (df_opps["division"] == division) &
            (df_opps["is_won"] == True)
        ]["amount"].sum()

        if actual > 0:
            error_pct        = np.random.normal(0, 0.13)
            forecast_committed = actual * (1 - error_pct)
            forecast_best_case = forecast_committed * random.uniform(1.08, 1.25)
        else:
            forecast_committed = 0
            forecast_best_case = 0

        forecast_rows.append({
            "fiscal_quarter":     q,
            "division":           division,
            "forecast_committed": round(forecast_committed, 2),
            "forecast_best_case": round(forecast_best_case, 2),
            "actual_bookings":    round(actual, 2),
            "variance_pct":       round(((actual - forecast_committed) / forecast_committed * 100), 1) if forecast_committed > 0 else None,
        })

df_forecast = pd.DataFrame(forecast_rows)

# ── 6. Date Dimension ─────────────────────────────────────────────────────
dates = pd.date_range(datetime(2024, 6, 1), datetime(2026, 12, 31), freq="D")
df_date = pd.DataFrame({"date": dates})
df_date["year"]           = df_date["date"].dt.year
df_date["month"]          = df_date["date"].dt.month
df_date["month_name"]     = df_date["date"].dt.strftime("%b")
df_date["month_year"]     = df_date["date"].dt.strftime("%b %Y")
df_date["quarter"]        = df_date["date"].dt.quarter
df_date["fiscal_quarter"] = "FY" + df_date["year"].astype(str) + "-Q" + df_date["quarter"].astype(str)
df_date["day_of_week"]    = df_date["date"].dt.day_name()

# ── Save ──────────────────────────────────────────────────────────────────
df_reps.to_csv("reps.csv", index=False)
df_accounts.drop(columns=["natural_products"]).to_csv("accounts.csv", index=False)
df_opps.to_csv("opportunities.csv", index=False)
df_quota.to_csv("quota_attainment.csv", index=False)
df_forecast.to_csv("forecast_accuracy.csv", index=False)
df_date.to_csv("date_dim.csv", index=False)

print("=== generate_data.py complete ===")
print(f"Reps:          {len(df_reps)}")
print(f"Accounts:      {len(df_accounts)}")
print(f"Opportunities: {len(df_opps)}")
print(f"  Closed Won:  {(df_opps['is_won']==True).sum()}")
print(f"  Closed Lost: {(df_opps['is_won']==False).sum()}")
print(f"  Open:        {df_opps['is_closed'].eq(False).sum()}")
print(f"  Stalled:     {df_opps['is_stalled'].sum()}")
print(f"Quota rows:    {len(df_quota)}")
print(f"Forecast rows: {len(df_forecast)}")
print(f"Date dim rows: {len(df_date)}")
print(f"\nTotal Bookings: ${df_opps[df_opps['is_won']==True]['amount'].sum():,.0f}")
