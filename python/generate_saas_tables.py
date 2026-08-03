"""
DFIN Sales Operations Dashboard — SaaS Metrics Generator
generate_saas_tables.py

Generates supplemental SaaS metrics tables from the base dataset:
  - subscriptions.csv       (ARR, churn, customer state per account)
  - arr_events.csv          (New / Expansion / Contraction / Churn / Renewal events)
  - nrr_summary.csv         (quarterly NRR and GRR by division)
  - marketing_spend.csv     (monthly S&M spend by channel and division)
  - cac_summary.csv         (quarterly CAC, LTV, payback — trailing 12-month)
  - arpu_arr_monthly.csv    (monthly ARR and ARPU trend)

Run AFTER generate_data.py — requires opportunities.csv and accounts.csv.

Usage: python generate_saas_tables.py
Requirements: pip install pandas numpy python-dateutil
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

random.seed(99)
np.random.seed(99)

TODAY      = datetime(2026, 6, 30)
DATA_START = datetime(2024, 7, 1)
RECURRING  = ["ActiveDisclosure", "Arc Suite"]

PRODUCT_CONFIG = {
    "ActiveDisclosure": {
        "avg_arr":         68_000,
        "arr_std":         22_000,
        "annual_churn":    0.07,
        "expansion_p":     0.18,
        "expansion_amt":   (5_000, 20_000),
        "contraction_p":   0.06,
        "contraction_amt": (3_000, 12_000),
        "gross_margin":    0.74,
    },
    "Arc Suite": {
        "avg_arr":         60_000,
        "arr_std":         18_000,
        "annual_churn":    0.06,
        "expansion_p":     0.14,
        "expansion_amt":   (4_000, 16_000),
        "contraction_p":   0.05,
        "contraction_amt": (3_000, 10_000),
        "gross_margin":    0.71,
    },
}

# ── Load base data ────────────────────────────────────────────────────────
opps     = pd.read_csv("opportunities.csv", parse_dates=["created_date", "close_date"])
accounts = pd.read_csv("accounts.csv")
won_opps = opps[opps["is_won"] == True].copy()
months   = pd.date_range(DATA_START, TODAY, freq="MS")

# ── 1. Subscriptions + ARR Events ─────────────────────────────────────────
sub_rows   = []
event_rows = []
sub_id     = 20000

for product, cfg in PRODUCT_CONFIG.items():
    prod_won = won_opps[won_opps["division"] == product].copy()
    prod_won = (
        prod_won.sort_values("close_date")
        .drop_duplicates(subset=["account_id"], keep="first")
        .merge(accounts[["account_id", "segment", "region"]], on="account_id", how="left")
    )

    monthly_churn = 1 - (1 - cfg["annual_churn"]) ** (1/12)

    for _, deal in prod_won.iterrows():
        start_dt    = deal["close_date"]
        if start_dt < DATA_START:
            start_dt = DATA_START

        initial_arr = max(20_000, np.random.normal(cfg["avg_arr"], cfg["arr_std"]))
        current_arr = initial_arr
        churned     = False
        churn_dt    = None
        cursor      = start_dt.replace(day=1)
        months_active = 0

        while cursor <= TODAY and not churned:
            if months_active > 3 and random.random() < monthly_churn:
                churned  = True
                churn_dt = cursor
                event_rows.append({
                    "account_id":    deal["account_id"],
                    "division":      product,
                    "event_month":   cursor,
                    "movement_type": "Churn",
                    "arr_change":    -current_arr,
                    "fiscal_quarter": f"FY{cursor.year}-Q{(cursor.month-1)//3+1}",
                })
                break

            if months_active > 0 and months_active % 12 == 0:
                roll = random.random()
                if roll < cfg["expansion_p"]:
                    delta = random.uniform(*cfg["expansion_amt"])
                    current_arr += delta
                    event_rows.append({
                        "account_id": deal["account_id"], "division": product,
                        "event_month": cursor, "movement_type": "Expansion",
                        "arr_change": delta,
                        "fiscal_quarter": f"FY{cursor.year}-Q{(cursor.month-1)//3+1}",
                    })
                elif roll < cfg["expansion_p"] + cfg["contraction_p"]:
                    delta = -random.uniform(*cfg["contraction_amt"])
                    current_arr = max(10_000, current_arr + delta)
                    event_rows.append({
                        "account_id": deal["account_id"], "division": product,
                        "event_month": cursor, "movement_type": "Contraction",
                        "arr_change": delta,
                        "fiscal_quarter": f"FY{cursor.year}-Q{(cursor.month-1)//3+1}",
                    })
                else:
                    event_rows.append({
                        "account_id": deal["account_id"], "division": product,
                        "event_month": cursor, "movement_type": "Renewal",
                        "arr_change": 0,
                        "fiscal_quarter": f"FY{cursor.year}-Q{(cursor.month-1)//3+1}",
                    })

            if months_active == 0:
                event_rows.append({
                    "account_id": deal["account_id"], "division": product,
                    "event_month": cursor, "movement_type": "New",
                    "arr_change": initial_arr,
                    "fiscal_quarter": f"FY{cursor.year}-Q{(cursor.month-1)//3+1}",
                })

            cursor += relativedelta(months=1)
            months_active += 1

        sub_rows.append({
            "subscription_id":   sub_id,
            "account_id":        deal["account_id"],
            "account_name":      deal["account_name"],
            "division":          product,
            "segment":           deal.get("segment_x", deal.get("segment", "")),
            "region":            deal.get("region_x",  deal.get("region",  "")),
            "subscription_start": start_dt.strftime("%Y-%m-%d"),
            "subscription_end":  churn_dt.strftime("%Y-%m-%d") if churned else None,
            "initial_arr":       round(initial_arr, 2),
            "current_arr":       round(current_arr if not churned else 0, 2),
            "mrr":               round((current_arr if not churned else 0) / 12, 2),
            "status":            "Churned" if churned else "Active",
            "cohort_quarter":    f"FY{start_dt.year}-Q{(start_dt.month-1)//3+1}",
            "gross_margin_pct":  cfg["gross_margin"],
            "months_active":     months_active,
        })
        sub_id += 1

df_subs   = pd.DataFrame(sub_rows)
df_events = pd.DataFrame(event_rows)

# ── 2. NRR Summary ────────────────────────────────────────────────────────
quarters_ordered = ["FY2024-Q3","FY2024-Q4","FY2025-Q1","FY2025-Q2",
                    "FY2025-Q3","FY2025-Q4","FY2026-Q1","FY2026-Q2"]
nrr_rows = []

for product in RECURRING:
    prod_events = df_events[df_events["division"] == product]
    prod_subs   = df_subs[df_subs["division"] == product]

    for q in quarters_ordered:
        q_year, q_num    = int(q[2:6]), int(q[-1])
        q_start_dt       = datetime(q_year, (q_num-1)*3+1, 1)

        new_arr         = prod_events[(prod_events["fiscal_quarter"]==q) & (prod_events["movement_type"]=="New")]["arr_change"].sum()
        expansion_arr   = prod_events[(prod_events["fiscal_quarter"]==q) & (prod_events["movement_type"]=="Expansion")]["arr_change"].sum()
        contraction_arr = prod_events[(prod_events["fiscal_quarter"]==q) & (prod_events["movement_type"]=="Contraction")]["arr_change"].sum()
        churn_arr       = prod_events[(prod_events["fiscal_quarter"]==q) & (prod_events["movement_type"]=="Churn")]["arr_change"].sum()

        active_at_start = prod_subs[
            (pd.to_datetime(prod_subs["subscription_start"]) < q_start_dt) &
            ((prod_subs["subscription_end"].isna()) |
             (pd.to_datetime(prod_subs["subscription_end"]) >= q_start_dt))
        ]
        starting_arr = active_at_start["initial_arr"].sum()
        ending_arr   = starting_arr + new_arr + expansion_arr + contraction_arr + churn_arr
        nrr = round(((starting_arr + expansion_arr + contraction_arr + churn_arr) / starting_arr * 100), 1) if starting_arr > 0 else None
        grr = round(((starting_arr + contraction_arr + churn_arr) / starting_arr * 100), 1) if starting_arr > 0 else None

        nrr_rows.append({
            "fiscal_quarter":  q,
            "division":        product,
            "starting_arr":    round(starting_arr, 2),
            "new_arr":         round(new_arr, 2),
            "expansion_arr":   round(expansion_arr, 2),
            "contraction_arr": round(contraction_arr, 2),
            "churn_arr":       round(churn_arr, 2),
            "ending_arr":      round(ending_arr, 2),
            "nrr_pct":         nrr,
            "grr_pct":         grr,
        })

df_nrr = pd.DataFrame(nrr_rows)

# ── 3. Marketing Spend ────────────────────────────────────────────────────
CHANNELS = {
    "Inbound / Content":    {"base_spend": 18_000, "lead_quality": 0.35, "opp_rate": 0.22, "win_rate": 0.38},
    "Outbound / SDR":       {"base_spend": 32_000, "lead_quality": 0.20, "opp_rate": 0.15, "win_rate": 0.28},
    "Events / Conferences": {"base_spend": 22_000, "lead_quality": 0.45, "opp_rate": 0.30, "win_rate": 0.42},
    "Partner / Referral":   {"base_spend":  8_000, "lead_quality": 0.60, "opp_rate": 0.42, "win_rate": 0.52},
    "Paid Digital":         {"base_spend": 14_000, "lead_quality": 0.18, "opp_rate": 0.10, "win_rate": 0.22},
}

spend_rows = []
for product in ["ActiveDisclosure", "Arc Suite", "Venue"]:
    mult = {"ActiveDisclosure": 1.0, "Arc Suite": 0.85, "Venue": 0.75}[product]
    for month in months:
        seasonal = 1.0 + 0.12 * np.sin((month.month / 12) * 2 * np.pi)
        for channel, cfg_ch in CHANNELS.items():
            spend = cfg_ch["base_spend"] * mult * seasonal * np.random.uniform(0.88, 1.14)
            leads = int(spend / 400 * cfg_ch["lead_quality"] * np.random.uniform(0.8, 1.2))
            opps_cnt = int(leads * cfg_ch["opp_rate"])
            wins  = int(opps_cnt * cfg_ch["win_rate"] * np.random.uniform(0.7, 1.3))
            spend_rows.append({
                "month":          month.strftime("%Y-%m-%d"),
                "division":       product,
                "channel":        channel,
                "spend":          round(spend, 2),
                "sourced_leads":  max(0, leads),
                "sourced_opps":   max(0, opps_cnt),
                "sourced_wins":   max(0, wins),
                "fiscal_quarter": f"FY{month.year}-Q{(month.month-1)//3+1}",
            })

df_spend = pd.DataFrame(spend_rows)

# ── 4. CAC Summary (trailing 12-month) ───────────────────────────────────
q_dates = {
    "FY2024-Q4": ("2024-10-01","2024-12-31"),
    "FY2025-Q1": ("2025-01-01","2025-03-31"),
    "FY2025-Q2": ("2025-04-01","2025-06-30"),
    "FY2025-Q3": ("2025-07-01","2025-09-30"),
    "FY2025-Q4": ("2025-10-01","2025-12-31"),
    "FY2026-Q1": ("2026-01-01","2026-03-31"),
    "FY2026-Q2": ("2026-04-01","2026-06-30"),
}

cac_rows = []
for product in ["ActiveDisclosure", "Arc Suite", "Venue"]:
    prod_spend_df = df_spend[df_spend["division"] == product]
    prod_won_df   = won_opps[won_opps["division"] == product].copy()
    prod_won_df["fiscal_quarter"] = prod_won_df["close_date"].apply(
        lambda d: f"FY{d.year}-Q{(d.month-1)//3+1}"
    )

    if product in PRODUCT_CONFIG:
        gm    = PRODUCT_CONFIG[product]["gross_margin"]
        churn = PRODUCT_CONFIG[product]["annual_churn"]
        arpu  = PRODUCT_CONFIG[product]["avg_arr"]
        ltv   = arpu * gm / churn
    else:
        gm, arpu = 0.62, 42_000
        ltv = arpu * gm * 2.5

    for q, (q_start, q_end) in q_dates.items():
        q_end_dt   = pd.to_datetime(q_end)
        t12_start  = q_end_dt - pd.DateOffset(months=12)

        spend_t12    = prod_spend_df[
            (pd.to_datetime(prod_spend_df["month"]) >= t12_start) &
            (pd.to_datetime(prod_spend_df["month"]) <= q_end_dt)
        ]["spend"].sum()

        new_logos_t12 = prod_won_df[
            (prod_won_df["close_date"] >= t12_start) &
            (prod_won_df["close_date"] <= q_end_dt) &
            (prod_won_df["is_renewal"] == False)
        ].shape[0]

        cac         = round(spend_t12 / new_logos_t12, 2) if new_logos_t12 > 0 else None
        cac_payback = round(cac / (arpu / 12 * gm), 1)   if cac else None
        ltv_cac     = round(ltv / cac, 2)                 if cac else None

        cac_rows.append({
            "fiscal_quarter":        q,
            "division":              product,
            "total_sm_spend_t12m":   round(spend_t12, 2),
            "new_logos_t12m":        new_logos_t12,
            "cac":                   cac,
            "arpu":                  arpu,
            "gross_margin_pct":      gm,
            "ltv":                   round(ltv, 2),
            "cac_payback_months":    cac_payback,
            "ltv_cac_ratio":         ltv_cac,
        })

df_cac = pd.DataFrame(cac_rows)

# ── 5. ARPU / ARR Monthly Snapshot ───────────────────────────────────────
arpu_rows = []
for product in RECURRING:
    prod_subs = df_subs[df_subs["division"] == product]
    for month in months:
        active = prod_subs[
            (pd.to_datetime(prod_subs["subscription_start"]) <= month) &
            ((prod_subs["subscription_end"].isna()) |
             (pd.to_datetime(prod_subs["subscription_end"]) > month))
        ]
        active_count = len(active)
        total_arr    = active["current_arr"].sum()
        arpu_rows.append({
            "month":            month.strftime("%Y-%m-%d"),
            "division":         product,
            "active_customers": active_count,
            "total_arr":        round(total_arr, 2),
            "mrr":              round(total_arr / 12, 2),
            "arpu":             round(total_arr / active_count, 2) if active_count > 0 else 0,
            "fiscal_quarter":   f"FY{month.year}-Q{(month.month-1)//3+1}",
        })

df_arpu = pd.DataFrame(arpu_rows)

# ── Save ──────────────────────────────────────────────────────────────────
df_subs.to_csv("subscriptions.csv",    index=False)
df_events.to_csv("arr_events.csv",     index=False)
df_nrr.to_csv("nrr_summary.csv",       index=False)
df_spend.to_csv("marketing_spend.csv", index=False)
df_cac.to_csv("cac_summary.csv",       index=False)
df_arpu.to_csv("arpu_arr_monthly.csv", index=False)

print("=== generate_saas_tables.py complete ===")
print(f"subscriptions.csv:    {len(df_subs):>5} rows  ({df_subs[df_subs['status']=='Active'].shape[0]} active, {df_subs[df_subs['status']=='Churned'].shape[0]} churned)")
print(f"arr_events.csv:       {len(df_events):>5} rows")
print(f"nrr_summary.csv:      {len(df_nrr):>5} rows")
print(f"marketing_spend.csv:  {len(df_spend):>5} rows")
print(f"cac_summary.csv:      {len(df_cac):>5} rows")
print(f"arpu_arr_monthly.csv: {len(df_arpu):>5} rows")
