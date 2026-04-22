import requests

def test_api():
    try:
        response = requests.get("http://localhost:8000/clinical/utentes")
        print(f"Status: {response.status_code}")
        utentes = response.json()
        print(f"Total utentes via API: {len(utentes)}")
        for u in utentes:
            if str(u.get('num_utente')) == '111111111':
                print(f"ENCONTRADO na API: {u}")
                return
        print("Utente 111111111 NÃO ENCONTRADO na resposta da API.")
    except Exception as e:
        print(f"Erro ao conectar: {e}")

if __name__ == "__main__":
    test_api()
