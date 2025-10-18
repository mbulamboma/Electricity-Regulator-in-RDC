#!/usr/bin/env python3
"""
Test rapide de l'API dédiée des filtres
"""

import requests

def test_api():
    base_url = "http://127.0.0.1:5000"

    print("Test de l'API dédiée: /production-thermique/api/filters")
    print("=" * 60)

    # Test sans paramètres
    try:
        response = requests.get(f"{base_url}/production-thermique/api/filters", timeout=5)
        print(f"✅ API accessible - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Clés retournées: {list(data.keys())}")
            print(f"   Nombre de rapports: {len(data.get('rapports', []))}")
            print(f"   Stats disponibles: {list(data.get('stats', {}).keys())}")
        elif response.status_code == 401:
            print("   ⚠️  Authentification requise (normal pour une API protégée)")
        else:
            print(f"   ❌ Status inattendu: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible - Démarrer avec: flask --app run run --debug")
    except Exception as e:
        print(f"❌ Erreur: {e}")

    print("\nTest terminé!")

if __name__ == "__main__":
    test_api()