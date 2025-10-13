#!/usr/bin/env python3
"""
Test Rapide de Santé de l'Application
=====================================

Script minimaliste pour vérifier rapidement que l'application fonctionne.
Idéal pour les tests de santé réguliers ou l'intégration continue.
"""

import requests
import time
from datetime import datetime
import sys

def test_app_health(base_url="http://localhost:5000"):
    """Test rapide de santé de l'application"""
    
    print(f"🏥 Test de santé - {datetime.now().strftime('%H:%M:%S')}")
    print(f"🎯 URL: {base_url}")
    print("="*50)
    
    # Tests critiques
    critical_routes = [
        ('/', 'Page d\'accueil'),
        ('/auth/login', 'Page de connexion'),
        ('/operateurs/', 'Liste opérateurs'),
        ('/production_hydro/', 'Production hydro'),
        ('/are/dashboard/', 'Dashboard ARE')
    ]
    
    success_count = 0
    total_time = 0
    
    for route, description in critical_routes:
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            response_time = time.time() - start_time
            total_time += response_time
            
            if response.status_code == 200:
                print(f"✅ {description}: OK ({response_time:.2f}s)")
                success_count += 1
            elif response.status_code == 302:
                print(f"🔄 {description}: Redirection ({response_time:.2f}s)")
                success_count += 1
            else:
                print(f"❌ {description}: Erreur {response.status_code} ({response_time:.2f}s)")
                
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            total_time += response_time
            print(f"💥 {description}: Exception - {e} ({response_time:.2f}s)")
    
    # Résultats
    print("="*50)
    success_rate = (success_count / len(critical_routes)) * 100
    avg_time = total_time / len(critical_routes)
    
    print(f"📊 Résultats: {success_count}/{len(critical_routes)} routes OK ({success_rate:.1f}%)")
    print(f"⏱️ Temps moyen: {avg_time:.2f}s")
    
    if success_rate >= 80:
        print("✅ Application en bonne santé")
        return True
    else:
        print("❌ Application défaillante")
        return False

def main():
    """Fonction principale"""
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    try:
        healthy = test_app_health(url)
        sys.exit(0 if healthy else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()