import requests
import json
from datetime import datetime, timedelta

# =====================================================
# 🔑 CONFIGURAÇÃO
# =====================================================
# NOTA: Este script foi integrado à API Django.
# Use o endpoint: GET /users/{user_id}/productads?period=30
# Para usar este script standalone, configure o ACCESS_TOKEN abaixo.

ACCESS_TOKEN = None  # Configure seu token aqui se quiser usar standalone

# PERÍODOS PERMITIDOS: 7, 15, 30, 60, 90
PERIOD_DAYS = 30   # 👈 padrão dashboard

BASE_URL = "https://api.mercadolibre.com"

if not ACCESS_TOKEN:
    raise ValueError(
        "ACCESS_TOKEN não configurado. "
        "Use a API Django: GET /users/{user_id}/productads?period=30"
    )

HEADERS_V1 = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Api-Version": "1"
}

HEADERS_V2 = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "api-version": "2"
}


# =====================================================
# VALIDAR PERÍODO
# =====================================================
def validate_period(days):
    allowed = [7, 15, 30, 60, 90]
    if days not in allowed:
        raise Exception(f"Período inválido. Use: {allowed}")
    return days


# =====================================================
# 1️⃣ PEGAR ADVERTISER E SITE
# =====================================================
def get_advertiser():
    url = f"{BASE_URL}/advertising/advertisers"
    params = {"product_id": "PADS"}

    r = requests.get(url, headers=HEADERS_V1, params=params)

    if r.status_code != 200:
        raise Exception(r.text)

    adv = r.json()["advertisers"][0]
    return adv["advertiser_id"], adv["site_id"]


# =====================================================
# 2️⃣ BUSCAR CAMPANHAS + MÉTRICAS
# =====================================================
def get_campaigns(advertiser_id, site_id, period_days):

    period_days = validate_period(period_days)

    date_to = datetime.today()
    date_from = date_to - timedelta(days=period_days)

    metrics = (
        "clicks,prints,cost,units_quantity,"
        "direct_amount,indirect_amount,total_amount,roas"
    )

    url = (
        f"{BASE_URL}/advertising/{site_id}/advertisers/"
        f"{advertiser_id}/product_ads/campaigns/search"
    )

    params = {
        "limit": 50,
        "offset": 0,
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
        "metrics": metrics
    }

    print(f"📅 Período selecionado: últimos {period_days} dias")

    r = requests.get(url, headers=HEADERS_V2, params=params)

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()["results"]


# =====================================================
# 3️⃣ GERAR RESUMO
# =====================================================
def build_dashboard_summary(campaigns):

    summary = {
        "investment": 0,
        "revenue": 0,
        "sales": 0,
        "impressions": 0,
        "clicks": 0
    }

    for c in campaigns:
        m = c.get("metrics", {})

        summary["investment"] += m.get("cost", 0)
        summary["revenue"] += m.get("total_amount", 0)
        summary["sales"] += m.get("units_quantity", 0)
        summary["impressions"] += m.get("prints", 0)
        summary["clicks"] += m.get("clicks", 0)

    summary["roas"] = (
        summary["revenue"] / summary["investment"]
        if summary["investment"] > 0 else 0
    )

    return summary


# =====================================================
# 🚀 EXECUÇÃO
# =====================================================
if __name__ == "__main__":

    print("🚀 Lendo Product Ads...\n")

    advertiser_id, site_id = get_advertiser()

    campaigns = get_campaigns(
        advertiser_id,
        site_id,
        PERIOD_DAYS
    )

    dashboard = build_dashboard_summary(campaigns)

    result = {
        "period_days": PERIOD_DAYS,
        "dashboard": dashboard,
        "campaigns": campaigns
    }

    print("\n✅ RESULTADO FINAL:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
