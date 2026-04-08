"""
Meta Ads Automation — Future Culture
--------------------------------------
Features:
  1. Create a new campaign (+ ad set + ad)
  2. Duplicate an existing campaign
  3. Turn campaigns on / off
  4. Pull performance reports

Usage:
  python meta_ads.py
"""

import sys
import json
from datetime import datetime
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative

# ─── CONFIG ────────────────────────────────────────────────────────────────────
ACCESS_TOKEN = "PASTE_YOUR_TOKEN_HERE"
AD_ACCOUNT_ID = "act_1611343746885970"
PAGE_ID = "PASTE_YOUR_PAGE_ID_HERE"   # e.g. "123456789"
# ───────────────────────────────────────────────────────────────────────────────


def init():
    FacebookAdsApi.init(access_token=ACCESS_TOKEN)
    return AdAccount(AD_ACCOUNT_ID)


# ── 1. CREATE CAMPAIGN ──────────────────────────────────────────────────────────

def create_campaign(account, name, objective="OUTCOME_SALES", daily_budget=1000, status="PAUSED"):
    """
    Creates a campaign + ad set + placeholder ad.

    daily_budget is in cents (1000 = $10.00)
    objective options: OUTCOME_SALES, OUTCOME_TRAFFIC, OUTCOME_AWARENESS, OUTCOME_LEADS
    status: PAUSED (safe default) or ACTIVE
    """
    print(f"\n[1/3] Creating campaign: {name}")
    campaign = account.create_campaign(fields=[], params={
        Campaign.Field.name: name,
        Campaign.Field.objective: objective,
        Campaign.Field.status: Campaign.Status.paused if status == "PAUSED" else Campaign.Status.active,
        Campaign.Field.special_ad_categories: [],
    })
    campaign_id = campaign["id"]
    print(f"      Campaign created → ID: {campaign_id}")

    print(f"[2/3] Creating ad set...")
    ad_set = account.create_ad_set(fields=[], params={
        AdSet.Field.name: f"{name} - Ad Set",
        AdSet.Field.campaign_id: campaign_id,
        AdSet.Field.daily_budget: daily_budget,
        AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
        AdSet.Field.optimization_goal: AdSet.OptimizationGoal.offsite_conversions,
        AdSet.Field.targeting: {
            "geo_locations": {"countries": ["US"]},
            "age_min": 18,
            "age_max": 65,
        },
        AdSet.Field.status: AdSet.Status.paused,
    })
    ad_set_id = ad_set["id"]
    print(f"      Ad set created  → ID: {ad_set_id}")

    print(f"[3/3] Creating placeholder ad...")
    creative = account.create_ad_creative(fields=[], params={
        AdCreative.Field.name: f"{name} - Creative",
        AdCreative.Field.object_story_spec: {
            "page_id": PAGE_ID,
            "link_data": {
                "message": "Check us out!",
                "link": "https://www.example.com",
                "name": name,
            },
        },
    })

    ad = account.create_ad(fields=[], params={
        Ad.Field.name: f"{name} - Ad",
        Ad.Field.adset_id: ad_set_id,
        Ad.Field.creative: {"creative_id": creative["id"]},
        Ad.Field.status: Ad.Status.paused,
    })
    print(f"      Ad created      → ID: {ad['id']}")
    print(f"\n✓ Campaign '{name}' fully created (status: PAUSED — safe to review before activating)\n")
    return campaign_id


# ── 2. DUPLICATE CAMPAIGN ───────────────────────────────────────────────────────

def duplicate_campaign(campaign_id, new_name=None):
    """Duplicates an existing campaign by ID."""
    campaign = Campaign(campaign_id)
    data = campaign.api_get(fields=[
        Campaign.Field.name,
        Campaign.Field.objective,
        Campaign.Field.status,
        Campaign.Field.special_ad_categories,
    ])

    name = new_name or f"{data[Campaign.Field.name]} (copy)"
    print(f"\nDuplicating campaign {campaign_id} → '{name}'")

    result = campaign.create_copy(params={
        "deep_copy": True,
        "status_option": "PAUSED",
        "rename_options": {"rename_suffix": " (copy)"},
    })
    new_id = result["copied_campaign_id"]
    print(f"✓ Duplicated → new campaign ID: {new_id}\n")
    return new_id


# ── 3. TOGGLE CAMPAIGNS ON / OFF ───────────────────────────────────────────────

def list_campaigns(account):
    """Returns all campaigns with their ID, name, and status."""
    campaigns = account.get_campaigns(fields=[
        Campaign.Field.id,
        Campaign.Field.name,
        Campaign.Field.status,
        Campaign.Field.effective_status,
    ])
    return list(campaigns)


def toggle_campaign(campaign_id, turn_on: bool):
    """Turn a campaign on (ACTIVE) or off (PAUSED)."""
    new_status = Campaign.Status.active if turn_on else Campaign.Status.paused
    campaign = Campaign(campaign_id)
    campaign.api_update(params={Campaign.Field.status: new_status})
    state = "ON (ACTIVE)" if turn_on else "OFF (PAUSED)"
    print(f"✓ Campaign {campaign_id} → {state}")


# ── 4. PERFORMANCE REPORTS ─────────────────────────────────────────────────────

def get_report(account, date_preset="last_7d", level="campaign"):
    """
    Pulls performance data.

    date_preset options:
      today, yesterday, last_7d, last_14d, last_30d,
      this_month, last_month

    level options: campaign, adset, ad
    """
    print(f"\nFetching report — {level} level — {date_preset}\n")
    params = {
        "date_preset": date_preset,
        "level": level,
    }
    fields = [
        "campaign_name",
        "adset_name",
        "ad_name",
        "impressions",
        "reach",
        "clicks",
        "spend",
        "cpc",
        "cpm",
        "ctr",
        "conversions",
        "cost_per_conversion",
        "roas",
    ]

    insights = account.get_insights(fields=fields, params=params)

    results = []
    for row in insights:
        results.append(dict(row))

    if not results:
        print("No data found for this period.")
        return results

    # Print a clean table
    print(f"{'Campaign':<35} {'Spend':>8} {'Impressions':>12} {'Clicks':>7} {'CTR':>6} {'Conv.':>6} {'ROAS':>6}")
    print("-" * 85)
    for r in results:
        print(
            f"{r.get('campaign_name', 'N/A'):<35}"
            f"  ${float(r.get('spend', 0)):>7.2f}"
            f"  {r.get('impressions', 0):>11}"
            f"  {r.get('clicks', 0):>6}"
            f"  {float(r.get('ctr', 0)):>5.2f}%"
            f"  {r.get('conversions', 0):>5}"
            f"  {r.get('roas', 'N/A'):>6}"
        )

    # Save to JSON
    filename = f"report_{level}_{date_preset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Report saved to {filename}\n")
    return results


# ── MENU ────────────────────────────────────────────────────────────────────────

def menu():
    account = init()

    while True:
        print("\n══════════════════════════════════")
        print("   Future Culture — Meta Ads CLI  ")
        print("══════════════════════════════════")
        print("  1. Create new campaign")
        print("  2. Duplicate existing campaign")
        print("  3. Toggle campaign on / off")
        print("  4. Performance report")
        print("  0. Exit")
        print("──────────────────────────────────")
        choice = input("Choose: ").strip()

        if choice == "1":
            name = input("Campaign name: ").strip()
            print("Objectives: OUTCOME_SALES, OUTCOME_TRAFFIC, OUTCOME_AWARENESS, OUTCOME_LEADS")
            objective = input("Objective [OUTCOME_SALES]: ").strip() or "OUTCOME_SALES"
            budget_input = input("Daily budget in $ [10]: ").strip() or "10"
            daily_budget = int(float(budget_input) * 100)  # convert to cents
            create_campaign(account, name, objective, daily_budget)

        elif choice == "2":
            campaigns = list_campaigns(account)
            print("\nYour campaigns:")
            for i, c in enumerate(campaigns):
                print(f"  {i+1}. [{c['id']}] {c['name']} — {c['status']}")
            idx = int(input("Pick number to duplicate: ").strip()) - 1
            new_name = input("New name (leave blank to auto-name): ").strip() or None
            duplicate_campaign(campaigns[idx]["id"], new_name)

        elif choice == "3":
            campaigns = list_campaigns(account)
            print("\nYour campaigns:")
            for i, c in enumerate(campaigns):
                print(f"  {i+1}. [{c['id']}] {c['name']} — {c['status']}")
            idx = int(input("Pick number: ").strip()) - 1
            action = input("Turn [on/off]: ").strip().lower()
            toggle_campaign(campaigns[idx]["id"], turn_on=(action == "on"))

        elif choice == "4":
            print("Presets: today, yesterday, last_7d, last_14d, last_30d, this_month, last_month")
            preset = input("Date preset [last_7d]: ").strip() or "last_7d"
            print("Levels: campaign, adset, ad")
            level = input("Level [campaign]: ").strip() or "campaign"
            get_report(account, preset, level)

        elif choice == "0":
            print("Bye!")
            sys.exit(0)

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    menu()
