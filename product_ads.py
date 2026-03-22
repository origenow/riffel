import requests
import json
from datetime import datetime, timedelta

# ==========================================
# 🔑 CONFIGURAÇÃO
# ==========================================
# NOTA: Este script foi integrado à API Django.
# Use o endpoint: GET /users/{user_id}/productads?period=30
# Para usar este script standalone, configure o ACCESS_TOKEN abaixo.

ACCESS_TOKEN = None  # Configure seu token aqui se quiser usar standalone

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


# ==========================================
# 1️⃣ PEGAR ADVERTISER + SITE_ID
# ==========================================
def get_advertiser():
    url = f"{BASE_URL}/advertising/advertisers"

    params = {
        "product_id": "PADS"
    }

    r = requests.get(url, headers=HEADERS_V1, params=params)

    if r.status_code != 200:
        raise Exception(f"Erro advertisers:\n{r.text}")

    data = r.json()["advertisers"][0]

    advertiser_id = data["advertiser_id"]
    site_id = data["site_id"]

    print(f"✅ Advertiser: {advertiser_id}")
    print(f"✅ Site: {site_id}")

    return advertiser_id, site_id


# ==========================================
# 2️⃣ BUSCAR CAMPANHAS + MÉTRICAS
# ==========================================
def get_campaigns(advertiser_id, site_id):

    date_to = datetime.today()
    date_from = date_to - timedelta(days=30)

    metrics = (
        "clicks,prints,ctr,cost,cpc,acos,cvr,roas,"
        "direct_amount,indirect_amount,total_amount,"
        "units_quantity"
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

    r = requests.get(url, headers=HEADERS_V2, params=params)

    if r.status_code != 200:
        raise Exception(f"Erro campanhas:\n{r.text}")

    return r.json()


# ==========================================
# 🚀 EXECUÇÃO
# ==========================================
if __name__ == "__main__":

    print("🚀 Lendo Product Ads...\n")

    advertiser_id, site_id = get_advertiser()

    campaigns = get_campaigns(advertiser_id, site_id)

    print("\n✅ RESULTADO JSON:\n")
    print(json.dumps(campaigns, indent=2, ensure_ascii=False))
