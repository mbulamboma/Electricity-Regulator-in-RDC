#!/usr/bin/env python3
"""
Script Principal de Test Complet
================================

Ce script orchestre l'exécution de tous les tests de l'application Flask
et génère un rapport consolidé.

Usage:
    python tests/run_all_tests.py
    python tests/run_all_tests.py --full-report
    python tests/run_all_tests.py --quick
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRunner:
    """Orchestrateur de tests"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        
    def check_app_running(self) -> bool:
        """Vérifie si l'application Flask est en cours d'exécution"""
        try:
            import requests
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def start_app_if_needed(self) -> bool:
        """Démarre l'application si elle n'est pas en cours d'exécution"""
        if self.check_app_running():
            print(f"✅ Application déjà en cours d'exécution sur {self.base_url}")
            return True
            
        print(f"🚀 Démarrage de l'application Flask...")
        # Note: En production, vous pourriez vouloir démarrer l'app automatiquement
        print(f"❌ Application non accessible sur {self.base_url}")
        print("   Veuillez démarrer l'application avec: flask --app run run --debug")
        return False
        
    def run_route_tests(self, quick: bool = False) -> dict:
        """Exécute les tests de routes"""
        print("\n🔗 Exécution des tests de routes...")
        start_time = time.time()
        
        try:
            # Importer et exécuter le testeur de routes
            from manual_test_routes import RouteTester
            
            tester = RouteTester(self.base_url)
            
            if quick:
                # Tests rapides - seulement les routes principales
                tester.test_common_routes()
                tester.test_auth_routes()
            else:
                # Tests complets
                tester.run_all_tests()
                
            execution_time = time.time() - start_time
            
            total_tests = len(tester.results)
            successful_tests = sum(1 for r in tester.results if r.success)
            
            result = {
                'total': total_tests,
                'success': successful_tests,
                'failed': total_tests - successful_tests,
                'execution_time': execution_time,
                'details': tester.results
            }
            
            print(f"   ✅ Tests de routes terminés: {successful_tests}/{total_tests} réussis en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            print(f"   ❌ Erreur dans les tests de routes: {e}")
            return {'error': str(e)}
            
    def run_form_tests(self) -> dict:
        """Exécute les tests de formulaires"""
        print("\n📝 Exécution des tests de formulaires...")
        start_time = time.time()
        
        try:
            # Importer et exécuter le testeur de formulaires
            from test_forms import FormTester
            
            tester = FormTester(self.base_url)
            tester.run_all_form_tests()
            
            execution_time = time.time() - start_time
            
            result = {
                'execution_time': execution_time,
                'status': 'completed'
            }
            
            print(f"   ✅ Tests de formulaires terminés en {execution_time:.1f}s")
            return result
            
        except Exception as e:
            print(f"   ❌ Erreur dans les tests de formulaires: {e}")
            return {'error': str(e)}
            
    def run_database_tests(self) -> dict:
        """Exécute des tests basiques sur la base de données"""
        print("\n🗄️ Vérification de la base de données...")
        start_time = time.time()
        
        try:
            # Test de connexion à la base de données
            from app import create_app
            from app.extensions import db
            from app.models.utilisateurs import User
            from app.models.operateurs import Operateur
            
            app = create_app()
            with app.app_context():
                # Test de requêtes basiques
                user_count = User.query.count()
                operateur_count = Operateur.query.count()
                
                execution_time = time.time() - start_time
                
                result = {
                    'user_count': user_count,
                    'operateur_count': operateur_count,
                    'execution_time': execution_time,
                    'status': 'success'
                }
                
                print(f"   ✅ Base de données OK: {user_count} utilisateurs, {operateur_count} opérateurs")
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   ❌ Erreur base de données: {e}")
            return {'error': str(e), 'execution_time': execution_time}
            
    def generate_consolidated_report(self, full_report: bool = False) -> str:
        """Génère un rapport consolidé de tous les tests"""
        report = f"""
{'='*80}
🧪 RAPPORT CONSOLIDÉ DE TESTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

🎯 APPLICATION TESTÉE: {self.base_url}

"""
        
        # Résumé des tests de routes
        if 'routes' in self.results and 'error' not in self.results['routes']:
            routes = self.results['routes']
            success_rate = (routes['success'] / routes['total'] * 100) if routes['total'] > 0 else 0
            report += f"""🔗 TESTS DE ROUTES:
   Total: {routes['total']} routes testées
   ✅ Succès: {routes['success']} ({success_rate:.1f}%)
   ❌ Échecs: {routes['failed']}
   ⏱️ Temps d'exécution: {routes['execution_time']:.1f}s

"""
        
        # Résumé des tests de formulaires
        if 'forms' in self.results and 'error' not in self.results['forms']:
            forms = self.results['forms']
            report += f"""📝 TESTS DE FORMULAIRES:
   ✅ Statut: {forms['status']}
   ⏱️ Temps d'exécution: {forms['execution_time']:.1f}s

"""
        
        # Résumé des tests de base de données
        if 'database' in self.results and 'error' not in self.results['database']:
            db_result = self.results['database']
            report += f"""🗄️ TESTS DE BASE DE DONNÉES:
   ✅ Statut: {db_result['status']}
   👥 Utilisateurs: {db_result.get('user_count', 'N/A')}
   🏢 Opérateurs: {db_result.get('operateur_count', 'N/A')}
   ⏱️ Temps d'exécution: {db_result['execution_time']:.1f}s

"""
        
        # Erreurs globales
        errors = []
        for test_type, result in self.results.items():
            if isinstance(result, dict) and 'error' in result:
                errors.append(f"{test_type}: {result['error']}")
                
        if errors:
            report += "❌ ERREURS DÉTECTÉES:\n"
            for error in errors:
                report += f"   • {error}\n"
            report += "\n"
            
        # Recommandations
        report += "💡 RECOMMANDATIONS:\n"
        
        if 'routes' in self.results and 'failed' in self.results['routes']:
            failed_routes = self.results['routes']['failed']
            if failed_routes > 0:
                report += f"   • Corriger {failed_routes} route(s) en échec\n"
                
        if errors:
            report += "   • Résoudre les erreurs d'exécution listées ci-dessus\n"
            
        report += "   • Exécuter les tests régulièrement après chaque modification\n"
        report += "   • Considérer l'ajout de tests unitaires avec pytest\n"
        
        # Détails complets si demandés
        if full_report and 'routes' in self.results and 'details' in self.results['routes']:
            report += "\n" + "="*50 + "\n"
            report += "📋 DÉTAILS DES TESTS DE ROUTES:\n"
            report += "="*50 + "\n"
            
            for result in self.results['routes']['details']:
                status_icon = "✅" if result.success else "❌"
                report += f"{status_icon} {result.method:6} {result.endpoint:40} "
                report += f"{result.status_code:3} ({result.response_time:.3f}s)"
                if result.description:
                    report += f" - {result.description}"
                if hasattr(result, 'error_message') and result.error_message:
                    report += f" | {result.error_message}"
                report += "\n"
                
        report += f"\n{'='*80}\n"
        return report
        
    def save_report(self, report: str, filename: str = None):
        """Sauvegarde le rapport consolidé"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tests/rapport_complet_{timestamp}.txt"
            
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"📄 Rapport sauvegardé: {filename}")
        
    def run_all_tests(self, quick: bool = False, full_report: bool = False):
        """Exécute tous les tests et génère le rapport"""
        print(f"🧪 DÉBUT DES TESTS COMPLETS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # Vérifier que l'application est accessible
        if not self.check_app_running():
            print("❌ Application non accessible. Tests annulés.")
            return
            
        # Exécuter les différents types de tests
        self.results['routes'] = self.run_route_tests(quick)
        
        if not quick:
            self.results['forms'] = self.run_form_tests()
            self.results['database'] = self.run_database_tests()
            
        # Générer et afficher le rapport
        report = self.generate_consolidated_report(full_report)
        print(report)
        
        # Sauvegarder le rapport
        self.save_report(report)
        
        print("🏁 Tests terminés!")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Tests complets de l\'application Flask')
    parser.add_argument('--url', default='http://localhost:5000',
                       help='URL de base de l\'application')
    parser.add_argument('--quick', action='store_true',
                       help='Tests rapides (routes principales seulement)')
    parser.add_argument('--full-report', action='store_true',
                       help='Rapport détaillé avec tous les résultats')
    parser.add_argument('--setup', action='store_true',
                       help='Installer les dépendances nécessaires')
    
    args = parser.parse_args()
    
    # Installation des dépendances si demandée
    if args.setup:
        print("📦 Installation des dépendances...")
        try:
            subprocess.check_call([sys.executable, 'tests/setup_test_env.py'])
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur installation: {e}")
            sys.exit(1)
        return
        
    # Exécuter les tests
    runner = TestRunner(args.url)
    runner.run_all_tests(args.quick, args.full_report)

if __name__ == "__main__":
    main()