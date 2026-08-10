#!/usr/bin/env python3

import sys
import json
import requests

BASE_URL = "http://0.0.0.0:8000/api/v1"

USERNAME = "admin"
PASSWORD = "admin"


if len(sys.argv) != 2:
    print(f"Uso: {sys.argv[0]} arquivo.json")
    sys.exit(1)

arquivo = sys.argv[1]

# --------------------------------------------------
# Lê JSON
# --------------------------------------------------

try:
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        dados = json.load(f)
except Exception as e:
    print(f"Erro ao ler JSON: {e}")
    sys.exit(1)


try:
    # --------------------------------------------------
    # Login
    # OAuth2PasswordRequestForm espera form-urlencoded
    # --------------------------------------------------

    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "username": USERNAME,
            "password": PASSWORD
        },
        timeout=10
    )

    if response.status_code != 200:
        print(f"Erro no login: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

    token_data = response.json()
    access_token = token_data["access_token"]

    print("Login OK")

    # --------------------------------------------------
    # Envia inventário
    # --------------------------------------------------

    response = requests.post(
        f"{BASE_URL}/inventario",
        json=dados,
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=30
    )

    print(f"Inventário: HTTP {response.status_code}")
    print(response.text)

except requests.RequestException as e:
    print(f"Erro de conexão: {e}")
    sys.exit(1)
except (KeyError, ValueError) as e:
    print(f"Resposta inválida do servidor: {e}")
    sys.exit(1)