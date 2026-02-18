import requests
import concurrent.futures
import json
import time
from datetime import datetime, timezone

ACCESS_TOKEN = "APP_USR-4943523961409438-021212-e3b4aa7caa6d2948a46b50c0aa096e95-533863251"
USER_ID = "533863251"

BASE_URL = "https://api.mercadolibre.com"
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}


def get_all_item_ids():
    item_ids = []
    offset = 0
    limit = 50

    while True:
        url = f"{BASE_URL}/users/{USER_ID}/items/search?offset={offset}&limit={limit}"
        response = requests.get(url, headers=HEADERS)
        data = response.json()

        results = data.get("results", [])
        if not results:
            break

        item_ids.extend(results)
        offset += limit

    return item_ids


def calcular_tts(start_time_str, sold_quantity):
    if sold_quantity == 0:
        return None

    data_criacao = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
    agora = datetime.now(timezone.utc)

    diferenca = agora - data_criacao
    horas = diferenca.total_seconds() / 3600

    if horas <= 0:
        return None

    tts = horas / sold_quantity
    return round(tts, 2)


def extrair_dados(item):
    atributos = {a["id"]: a.get("value_name") for a in item.get("attributes", [])}

    marca = atributos.get("BRAND")
    gtin = atributos.get("GTIN")
    sku = atributos.get("SELLER_SKU")

    primeira_foto = None
    if item.get("pictures"):
        primeira_foto = item["pictures"][0].get("secure_url")

    tts = calcular_tts(item.get("start_time"), item.get("sold_quantity", 0))

    return {
        "ID": item.get("id"),
        "título": item.get("title"),
        "preço": item.get("price"),
        "estoque_atual": item.get("available_quantity"),
        "quantidade_vendida": item.get("sold_quantity"),
        "data_de_criacao": item.get("start_time"),
        "permalink": item.get("permalink"),
        "foto": primeira_foto,
        "modo_de_compra": item.get("shipping", {}).get("mode"),
        "tipo_logistico": item.get("shipping", {}).get("logistic_type"),
        "Marca": marca,
        "GTIN": gtin,
        "SKU": sku,
        "TTS_horas": tts
    }


def get_item_detail(item_id):
    url = f"{BASE_URL}/items/{item_id}"
    response = requests.get(url, headers=HEADERS)
    item = response.json()
    return extrair_dados(item)


def main():
    inicio = time.time()

    item_ids = get_all_item_ids()

    produtos = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(get_item_detail, item_ids)
        for item in results:
            produtos.append(item)

    # 🔥 Ordenar do menor TTS para o maior
    produtos.sort(
        key=lambda x: (x["TTS_horas"] is None, x["TTS_horas"])
    )

    final_json = {
        "total_produtos": len(produtos),
        "produtos": produtos
    }

    with open("produtos_meli_filtrado.json", "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

    print(f"Finalizado em {round(time.time() - inicio, 2)} segundos")
    return final_json



if __name__ == "__main__":
    resultado = main()
