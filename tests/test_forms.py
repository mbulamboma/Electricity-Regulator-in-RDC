#!/usr/bin/env python3
"""
Script de Test des Formulaires - Application Régulation Électricité RDC
=======================================================================

Ce script teste spécifiquement les formulaires de l'application avec
des données valides et invalides pour identifier les problèmes de validation.
"""

import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, date
from bs4 import BeautifulSoup
import random
import string

class FormTester:
    """Testeur spécialisé pour les formulaires"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.csrf_token = None
        self.test_results = []
        
    def get_csrf_token(self, url: str) -> Optional[str]:
        """Récupère le token CSRF d'une page"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            return csrf_input.get('value') if csrf_input else None
        except Exception:
            return None
            
    def test_operateur_form(self):
        """Test du formulaire de création d'opérateur"""
        print("🏢 Test formulaire Opérateur...")
        
        # Données valides
        valid_data = {
            'nom': 'Test Opérateur SARL',
            'type_operateur': 'production',
            'statut_licence': 'active',
            'date_licence': '2024-01-15',
            'adresse': '123 Avenue de la Paix, Kinshasa',
            'telephone': '+243 81 123 4567',
            'email': 'contact@testoperateur.cd',
            'description': 'Opérateur de test pour validation',
            'submit': 'Enregistrer'
        }
        
        # Données invalides
        invalid_data = {
            'nom': '',  # Nom vide
            'type_operateur': 'type_invalide',
            'email': 'email_invalide',
            'telephone': '123',  # Trop court
            'submit': 'Enregistrer'
        }
        
        self._test_form('/operateurs/nouveau', '/operateurs/', valid_data, invalid_data, "Opérateur")
        
    def test_centrale_hydro_form(self):
        """Test du formulaire de centrale hydro"""
        print("💧 Test formulaire Centrale Hydro...")
        
        valid_data = {
            'nom': 'Centrale Test Hydro',
            'operateur_id': '1',
            'localisation': 'Rivière Test, Province Test',
            'puissance_installee': '150.5',
            'production_annuelle': '500000',
            'hauteur_chute': '75.2',
            'debit_equipement': '125.8',
            'type_turbine': 'francis',
            'date_mise_service': '2023-06-15',
            'statut': 'operationnelle',
            'submit': 'Enregistrer'
        }
        
        invalid_data = {
            'nom': '',
            'puissance_installee': '-50',  # Valeur négative
            'production_annuelle': 'pas_un_nombre',
            'hauteur_chute': '',
            'submit': 'Enregistrer'
        }
        
        self._test_form('/production_hydro/nouvelle', '/production_hydro/', valid_data, invalid_data, "Centrale Hydro")
        
    def test_reseau_distribution_form(self):
        """Test du formulaire de réseau de distribution"""
        print("🏘️ Test formulaire Réseau Distribution...")
        
        valid_data = {
            'nom': 'Réseau Test Distribution',
            'code': 'RTD_001',
            'operateur_id': '1',
            'zone_couverture': 'Zone Test, Kinshasa',
            'tension_nominale': '15000',
            'longueur_totale': '125.75',
            'nombre_clients': '2500',
            'type_reseau': 'urbain',
            'date_creation': '2023-01-10',
            'submit': 'Enregistrer'
        }
        
        invalid_data = {
            'nom': '',
            'code': '',  # Code vide
            'tension_nominale': '-1000',  # Valeur négative
            'nombre_clients': 'abc',  # Pas un nombre
            'submit': 'Enregistrer'
        }
        
        self._test_form('/distribution/nouveau', '/distribution/', valid_data, invalid_data, "Réseau Distribution")
        
    def test_kpi_form(self):
        """Test du formulaire de KPI ARE"""
        print("📊 Test formulaire KPI ARE...")
        
        valid_data = {
            'code': 'TEST_KPI_001',
            'nom': 'KPI Test Automatique',
            'description': 'KPI créé pour les tests automatiques',
            'unite': '%',
            'periode': 'mensuelle',
            'objectif': '85.5',
            'seuil_alerte': '70.0',
            'source_donnees': 'Tests automatiques',
            'submit': 'Enregistrer'
        }
        
        invalid_data = {
            'code': '',  # Code vide
            'nom': '',   # Nom vide
            'objectif': 'pas_un_nombre',
            'seuil_alerte': '-10',  # Valeur négative
            'submit': 'Enregistrer'
        }
        
        self._test_form('/are/dashboard/kpis/nouveau', '/are/dashboard/kpis/', valid_data, invalid_data, "KPI ARE")
        
    def test_user_form(self):
        """Test du formulaire de création d'utilisateur"""
        print("👤 Test formulaire Utilisateur...")
        
        valid_data = {
            'nom_utilisateur': f'testuser_{random.randint(1000, 9999)}',
            'email': f'test{random.randint(100, 999)}@test.cd',
            'mot_de_passe': 'MotDePasseSecure123!',
            'confirmer_mot_de_passe': 'MotDePasseSecure123!',
            'role': 'operateur',
            'actif': True,
            'submit': 'Créer'
        }
        
        invalid_data = {
            'nom_utilisateur': '',  # Nom vide
            'email': 'email_invalide',
            'mot_de_passe': '123',  # Trop court
            'confirmer_mot_de_passe': '456',  # Différent
            'submit': 'Créer'
        }
        
        self._test_form('/admin/utilisateurs/nouveau', '/admin/utilisateurs/', valid_data, invalid_data, "Utilisateur")
        
    def test_workflow_form(self):
        """Test du formulaire de workflow"""
        print("📋 Test formulaire Workflow...")
        
        valid_data = {
            'titre': 'Workflow Test Automatique',
            'description': 'Workflow créé pour les tests',
            'type_rapport': 'production',
            'date_echeance': (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'priorite': '2',
            'assigné_à': '1',
            'submit': 'Créer'
        }
        
        invalid_data = {
            'titre': '',  # Titre vide
            'type_rapport': 'type_invalide',
            'date_echeance': '2020-01-01',  # Date passée
            'submit': 'Créer'
        }
        
        self._test_form('/workflow/nouveau', '/workflow/', valid_data, invalid_data, "Workflow")
        
    def _test_form(self, form_url: str, submit_url: str, valid_data: Dict, 
                   invalid_data: Dict, form_name: str):
        """Test générique d'un formulaire"""
        
        # Test 1: Accès au formulaire
        full_form_url = self.base_url + form_url
        try:
            response = self.session.get(full_form_url)
            if response.status_code == 200:
                print(f"  ✅ Accès formulaire {form_name}: OK")
                # Extraire le token CSRF
                self.csrf_token = self.get_csrf_token(full_form_url)
            else:
                print(f"  ❌ Accès formulaire {form_name}: {response.status_code}")
                return
        except Exception as e:
            print(f"  ❌ Erreur accès formulaire {form_name}: {e}")
            return
            
        # Test 2: Soumission avec données valides
        if self.csrf_token:
            valid_data['csrf_token'] = self.csrf_token
            
        try:
            response = self.session.post(self.base_url + submit_url, data=valid_data)
            if response.status_code in [200, 302]:  # 302 = redirection après succès
                print(f"  ✅ Soumission valide {form_name}: OK")
            else:
                print(f"  ⚠️ Soumission valide {form_name}: {response.status_code}")
                # Analyser le contenu pour les erreurs
                if 'error' in response.text.lower() or 'erreur' in response.text.lower():
                    print(f"    Contenu contient des erreurs")
        except Exception as e:
            print(f"  ❌ Erreur soumission valide {form_name}: {e}")
            
        # Test 3: Soumission avec données invalides
        if self.csrf_token:
            invalid_data['csrf_token'] = self.csrf_token
            
        try:
            response = self.session.post(self.base_url + submit_url, data=invalid_data)
            # Pour les données invalides, on s'attend à un statut 200 avec erreurs
            if response.status_code == 200:
                if 'error' in response.text.lower() or 'erreur' in response.text.lower():
                    print(f"  ✅ Validation invalide {form_name}: Erreurs détectées")
                else:
                    print(f"  ⚠️ Validation invalide {form_name}: Pas d'erreurs affichées")
            else:
                print(f"  ⚠️ Données invalides {form_name}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Erreur test invalide {form_name}: {e}")
            
        print()  # Ligne vide pour la lisibilité
        
    def run_all_form_tests(self):
        """Exécute tous les tests de formulaires"""
        print(f"\n🧪 TESTS DE FORMULAIRES - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # S'authentifier d'abord
        print("🔐 Authentification...")
        auth_url = self.base_url + '/auth/login'
        csrf_token = self.get_csrf_token(auth_url)
        
        auth_data = {
            'nom_utilisateur': 'admin',
            'mot_de_passe': 'admin123',
            'csrf_token': csrf_token,
            'submit': 'Se connecter'
        }
        
        response = self.session.post(auth_url, data=auth_data)
        if response.status_code in [200, 302]:
            print("  ✅ Authentification réussie\n")
        else:
            print("  ❌ Échec authentification\n")
            
        # Exécuter tous les tests de formulaires
        test_methods = [
            self.test_operateur_form,
            self.test_centrale_hydro_form,
            self.test_reseau_distribution_form,
            self.test_kpi_form,
            self.test_user_form,
            # self.test_workflow_form,  # Commenté car peut nécessiter des imports supplémentaires
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(1)  # Pause entre les tests
            except Exception as e:
                print(f"❌ Erreur dans {test_method.__name__}: {e}\n")

def main():
    """Fonction principale pour les tests de formulaires"""
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # Vérifier que l'application est accessible
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Application accessible sur {url}")
    except Exception as e:
        print(f"❌ Impossible d'accéder à {url}: {e}")
        sys.exit(1)
        
    # Exécuter les tests
    tester = FormTester(url)
    tester.run_all_form_tests()
    
    print("🏁 Tests de formulaires terminés")

if __name__ == "__main__":
    # Import nécessaire pour les dates
    from datetime import timedelta
    main()