#!/usr/bin/env python3
"""
Script de Test Manuel Complet pour l'Application de Régulation Électricité RDC
==============================================================================

Ce script teste automatiquement toutes les routes de l'application Flask
comme le ferait un utilisateur humain, identifie les erreurs et génère
un rapport détaillé.

Usage:
    python tests/manual_test_routes.py
    python tests/manual_test_routes.py --url http://localhost:5000
    python tests/manual_test_routes.py --auth-user admin --auth-pass admin123
"""

import requests
import json
import time
import argparse
import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import warnings

# Supprimer les warnings SSL pour les tests
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class Colors:
    """Codes couleur pour l'affichage console"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class TestResult:
    """Résultat d'un test de route"""
    def __init__(self, method: str, endpoint: str, status_code: int, 
                 response_time: float, description: str = ""):
        self.method = method
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_time = response_time
        self.description = description
        self.error_message = ""
        self.success = status_code < 400
        self.timestamp = datetime.now()
        
    def __str__(self):
        status_color = Colors.GREEN if self.success else Colors.RED
        return (f"{status_color}{self.method} {self.endpoint}: "
               f"{self.status_code} ({self.response_time:.2f}s){Colors.END}")

class RouteTester:
    """Testeur automatique de routes Flask"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results: List[TestResult] = []
        self.errors: List[str] = []
        self.csrf_token = None
        self.authenticated = False
        
        # Headers par défaut
        self.session.headers.update({
            'User-Agent': 'RouteTester/1.0 (Automated Testing Tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def log(self, message: str, color: str = Colors.WHITE):
        """Log avec couleur"""
        print(f"{color}{message}{Colors.END}")
        
    def extract_csrf_token(self, html_content: str) -> Optional[str]:
        """Extrait le token CSRF d'une page HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input:
                return csrf_input.get('value')
            
            # Alternative: chercher dans les meta tags
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                return csrf_meta.get('content')
        except Exception as e:
            self.log(f"Erreur extraction CSRF: {e}", Colors.YELLOW)
        return None
        
    def test_route(self, method: str, endpoint: str, 
                   data: Optional[Dict] = None, 
                   headers: Optional[Dict] = None,
                   expected_status: int = 200,
                   description: str = "",
                   follow_redirects: bool = True) -> TestResult:
        """Test une route individuelle"""
        
        url = urljoin(self.base_url, endpoint)
        start_time = time.time()
        
        try:
            # Préparer les headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
                
            # Ajouter CSRF token si nécessaire pour POST/PUT/DELETE
            if method.upper() in ['POST', 'PUT', 'DELETE'] and data and self.csrf_token:
                if isinstance(data, dict):
                    data['csrf_token'] = self.csrf_token
                    
            # Faire la requête
            response = self.session.request(
                method=method.upper(),
                url=url,
                data=data,
                headers=request_headers,
                allow_redirects=follow_redirects,
                timeout=30,
                verify=False  # Pour les tests locaux
            )
            
            response_time = time.time() - start_time
            
            # Créer le résultat
            result = TestResult(
                method=method.upper(),
                endpoint=endpoint,
                status_code=response.status_code,
                response_time=response_time,
                description=description
            )
            
            # Vérifier le statut attendu
            if response.status_code != expected_status and expected_status != 0:
                result.success = False
                result.error_message = f"Status attendu: {expected_status}, reçu: {response.status_code}"
                
            # Extraire CSRF token si c'est une page HTML
            if 'text/html' in response.headers.get('content-type', ''):
                csrf_token = self.extract_csrf_token(response.text)
                if csrf_token:
                    self.csrf_token = csrf_token
                    
            self.results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            result = TestResult(
                method=method.upper(),
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                description=description
            )
            result.success = False
            result.error_message = str(e)
            self.results.append(result)
            return result
            
    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """S'authentifier sur l'application"""
        self.log(f"🔐 Authentification avec {username}...", Colors.CYAN)
        
        # 1. Obtenir la page de login
        login_result = self.test_route('GET', '/auth/login', description="Page de login")
        if not login_result.success:
            self.log("❌ Impossible d'accéder à la page de login", Colors.RED)
            return False
            
        # 2. Tenter la connexion
        login_data = {
            'nom_utilisateur': username,
            'mot_de_passe': password,
            'submit': 'Se connecter'
        }
        
        auth_result = self.test_route(
            'POST', '/auth/login', 
            data=login_data,
            expected_status=302,  # Redirection attendue
            description="Tentative d'authentification"
        )
        
        if auth_result.status_code in [200, 302]:
            self.authenticated = True
            self.log("✅ Authentification réussie", Colors.GREEN)
            return True
        else:
            self.log(f"❌ Échec authentification: {auth_result.status_code}", Colors.RED)
            return False
            
    def test_auth_routes(self):
        """Test toutes les routes d'authentification"""
        self.log("\n🔐 === TEST DES ROUTES D'AUTHENTIFICATION ===", Colors.BOLD + Colors.CYAN)
        
        routes = [
            ('GET', '/auth/login', 200, "Page de connexion"),
            ('GET', '/auth/register', 200, "Page d'inscription"),
            ('GET', '/auth/logout', 302, "Déconnexion"),
            ('POST', '/auth/login', 0, "Connexion POST (test sans données)"),
            ('POST', '/auth/register', 0, "Inscription POST (test sans données)"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_operateurs_routes(self):
        """Test toutes les routes des opérateurs"""
        self.log("\n🏢 === TEST DES ROUTES OPÉRATEURS ===", Colors.BOLD + Colors.BLUE)
        
        routes = [
            ('GET', '/operateurs/', 200, "Liste des opérateurs"),
            ('GET', '/operateurs/nouveau', 200, "Nouveau opérateur"),
            ('GET', '/operateurs/1', 200, "Détail opérateur ID 1"),
            ('GET', '/operateurs/1/modifier', 200, "Modifier opérateur ID 1"),
            ('POST', '/operateurs/', 0, "Créer opérateur (sans données)"),
            ('POST', '/operateurs/1/modifier', 0, "Modifier opérateur (sans données)"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_production_routes(self):
        """Test toutes les routes de production"""
        self.log("\n⚡ === TEST DES ROUTES DE PRODUCTION ===", Colors.BOLD + Colors.YELLOW)
        
        # Production Hydro
        self.log("\n💧 Routes Production Hydro:", Colors.CYAN)
        hydro_routes = [
            ('GET', '/production_hydro/', 200, "Liste centrales hydro"),
            ('GET', '/production_hydro/nouvelle', 200, "Nouvelle centrale hydro"),
            ('GET', '/production_hydro/1', 200, "Détail centrale hydro ID 1"),
            ('GET', '/production_hydro/1/modifier', 200, "Modifier centrale hydro"),
            ('POST', '/production_hydro/', 0, "Créer centrale hydro"),
        ]
        
        for method, endpoint, expected, desc in hydro_routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"    {result}", Colors.WHITE)
            
        # Production Thermique
        self.log("\n🔥 Routes Production Thermique:", Colors.CYAN)
        thermique_routes = [
            ('GET', '/production_thermique/', 200, "Liste centrales thermiques"),
            ('GET', '/production_thermique/nouvelle', 200, "Nouvelle centrale thermique"),
            ('GET', '/production_thermique/1', 200, "Détail centrale thermique ID 1"),
            ('GET', '/production_thermique/1/modifier', 200, "Modifier centrale thermique"),
        ]
        
        for method, endpoint, expected, desc in thermique_routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"    {result}", Colors.WHITE)
            
        # Production Solaire
        self.log("\n☀️ Routes Production Solaire:", Colors.CYAN)
        solaire_routes = [
            ('GET', '/production_solaire/', 200, "Liste centrales solaires"),
            ('GET', '/production_solaire/nouvelle', 200, "Nouvelle centrale solaire"),
            ('GET', '/production_solaire/1', 200, "Détail centrale solaire ID 1"),
            ('GET', '/production_solaire/1/modifier', 200, "Modifier centrale solaire"),
        ]
        
        for method, endpoint, expected, desc in solaire_routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"    {result}", Colors.WHITE)
            
    def test_transport_routes(self):
        """Test toutes les routes de transport"""
        self.log("\n🔌 === TEST DES ROUTES TRANSPORT ===", Colors.BOLD + Colors.MAGENTA)
        
        routes = [
            ('GET', '/transport/', 200, "Liste lignes de transport"),
            ('GET', '/transport/nouvelle', 200, "Nouvelle ligne de transport"),
            ('GET', '/transport/1', 200, "Détail ligne ID 1"),
            ('GET', '/transport/1/modifier', 200, "Modifier ligne de transport"),
            ('POST', '/transport/', 0, "Créer ligne de transport"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_distribution_routes(self):
        """Test toutes les routes de distribution"""
        self.log("\n🏘️ === TEST DES ROUTES DISTRIBUTION ===", Colors.BOLD + Colors.GREEN)
        
        routes = [
            ('GET', '/distribution/', 200, "Liste réseaux de distribution"),
            ('GET', '/distribution/nouveau', 200, "Nouveau réseau de distribution"),
            ('GET', '/distribution/1', 200, "Détail réseau ID 1"),
            ('GET', '/distribution/1/modifier', 200, "Modifier réseau"),
            ('GET', '/distribution/postes/', 200, "Liste postes de distribution"),
            ('GET', '/distribution/postes/nouveau', 200, "Nouveau poste"),
            ('GET', '/distribution/postes/1', 200, "Détail poste ID 1"),
            ('POST', '/distribution/', 0, "Créer réseau de distribution"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_workflow_routes(self):
        """Test toutes les routes de workflow"""
        self.log("\n📋 === TEST DES ROUTES WORKFLOW ===", Colors.BOLD + Colors.CYAN)
        
        routes = [
            ('GET', '/workflow/', 200, "Liste des workflows"),
            ('GET', '/workflow/nouveau', 200, "Nouveau workflow"),
            ('GET', '/workflow/1', 200, "Détail workflow ID 1"),
            ('GET', '/workflow/1/valider', 200, "Valider workflow"),
            ('GET', '/workflow/1/rejeter', 200, "Rejeter workflow"),
            ('POST', '/workflow/', 0, "Créer workflow"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_notifications_routes(self):
        """Test toutes les routes de notifications"""
        self.log("\n🔔 === TEST DES ROUTES NOTIFICATIONS ===", Colors.BOLD + Colors.YELLOW)
        
        routes = [
            ('GET', '/notifications/', 200, "Liste notifications"),
            ('GET', '/notifications/non_lues', 200, "Notifications non lues"),
            ('GET', '/notifications/1/marquer_lue', 200, "Marquer notification lue"),
            ('POST', '/notifications/marquer_toutes_lues', 0, "Marquer toutes lues"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_contacts_routes(self):
        """Test toutes les routes de contacts"""
        self.log("\n👥 === TEST DES ROUTES CONTACTS ===", Colors.BOLD + Colors.BLUE)
        
        routes = [
            ('GET', '/contacts/', 200, "Liste contacts"),
            ('GET', '/contacts/nouveau', 200, "Nouveau contact"),
            ('GET', '/contacts/1', 200, "Détail contact ID 1"),
            ('GET', '/contacts/1/modifier', 200, "Modifier contact"),
            ('POST', '/contacts/', 0, "Créer contact"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_admin_routes(self):
        """Test toutes les routes d'administration"""
        self.log("\n👨‍💼 === TEST DES ROUTES ADMIN ===", Colors.BOLD + Colors.RED)
        
        routes = [
            ('GET', '/admin/', 200, "Dashboard admin"),
            ('GET', '/admin/utilisateurs', 200, "Gestion utilisateurs"),
            ('GET', '/admin/utilisateurs/nouveau', 200, "Nouvel utilisateur"),
            ('GET', '/admin/logs', 200, "Logs système"),
            ('GET', '/admin/config', 200, "Configuration"),
            ('POST', '/admin/utilisateurs/', 0, "Créer utilisateur"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_are_routes(self):
        """Test toutes les routes ARE (Autorité de Régulation)"""
        self.log("\n🏛️ === TEST DES ROUTES ARE ===", Colors.BOLD + Colors.MAGENTA)
        
        routes = [
            ('GET', '/are/', 200, "Dashboard ARE"),
            ('GET', '/are/dashboard/', 200, "Dashboard ARE détaillé"),
            ('GET', '/are/dashboard/kpis', 200, "Liste KPIs"),
            ('GET', '/are/dashboard/kpis/nouveau', 200, "Nouveau KPI"),
            ('GET', '/are/dashboard/kpis/1', 200, "Détail KPI ID 1"),
            ('GET', '/are/rapports/', 200, "Rapports ARE"),
            ('GET', '/are/analyses/', 200, "Analyses ARE"),
            ('POST', '/are/dashboard/kpis/', 0, "Créer KPI"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_common_routes(self):
        """Test les routes communes (/, /about, etc.)"""
        self.log("\n🏠 === TEST DES ROUTES COMMUNES ===", Colors.BOLD + Colors.WHITE)
        
        routes = [
            ('GET', '/', 200, "Page d'accueil"),
            ('GET', '/about', 200, "Page À propos"),
            ('GET', '/contact', 200, "Page Contact"),
            ('GET', '/static/css/style.css', 200, "CSS principal"),
            ('GET', '/static/js/main.js', 200, "JavaScript principal"),
            ('GET', '/favicon.ico', 0, "Favicon"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def test_error_routes(self):
        """Test les routes d'erreur intentionnelles"""
        self.log("\n❌ === TEST DES ROUTES D'ERREUR ===", Colors.BOLD + Colors.RED)
        
        routes = [
            ('GET', '/route_inexistante', 404, "Route inexistante"),
            ('GET', '/operateurs/999999', 404, "Opérateur inexistant"),
            ('GET', '/production_hydro/999999', 404, "Centrale inexistante"),
            ('POST', '/route_post_inexistante', 404, "POST sur route inexistante"),
        ]
        
        for method, endpoint, expected, desc in routes:
            result = self.test_route(method, endpoint, expected_status=expected, description=desc)
            self.log(f"  {result}", Colors.WHITE)
            
    def run_all_tests(self, authenticate_first: bool = True, 
                     username: str = "admin", password: str = "admin123"):
        """Exécute tous les tests"""
        self.log(f"\n🚀 DÉBUT DES TESTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                Colors.BOLD + Colors.GREEN)
        self.log(f"🎯 URL de base: {self.base_url}", Colors.CYAN)
        
        # Authentification si demandée
        if authenticate_first:
            success = self.authenticate(username, password)
            if not success:
                self.log("⚠️ Échec authentification, continuation sans auth", Colors.YELLOW)
                
        # Exécution de tous les tests
        test_methods = [
            self.test_common_routes,
            self.test_auth_routes,
            self.test_operateurs_routes,
            self.test_production_routes,
            self.test_transport_routes,
            self.test_distribution_routes,
            self.test_workflow_routes,
            self.test_notifications_routes,
            self.test_contacts_routes,
            self.test_admin_routes,
            self.test_are_routes,
            self.test_error_routes,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # Pause entre les groupes de tests
            except Exception as e:
                self.log(f"❌ Erreur dans {test_method.__name__}: {e}", Colors.RED)
                self.errors.append(f"{test_method.__name__}: {e}")
                
    def generate_report(self) -> str:
        """Génère un rapport détaillé des tests"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Calculs de statistiques
        avg_response_time = sum(r.response_time for r in self.results) / total_tests if total_tests > 0 else 0
        max_response_time = max((r.response_time for r in self.results), default=0)
        min_response_time = min((r.response_time for r in self.results), default=0)
        
        # Grouper les erreurs par code de statut
        error_codes = {}
        for result in self.results:
            if not result.success:
                code = result.status_code
                if code not in error_codes:
                    error_codes[code] = []
                error_codes[code].append(result)
                
        report = f"""
{'='*80}
📊 RAPPORT DE TEST DES ROUTES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

🎯 RÉSUMÉ GÉNÉRAL:
   URL testée: {self.base_url}
   Total des tests: {total_tests}
   ✅ Succès: {successful_tests} ({successful_tests/total_tests*100:.1f}%)
   ❌ Échecs: {failed_tests} ({failed_tests/total_tests*100:.1f}%)

⏱️ PERFORMANCE:
   Temps de réponse moyen: {avg_response_time:.3f}s
   Temps minimum: {min_response_time:.3f}s
   Temps maximum: {max_response_time:.3f}s

"""

        if error_codes:
            report += "❌ ERREURS PAR CODE DE STATUT:\n"
            for code, results in sorted(error_codes.items()):
                report += f"   {code}: {len(results)} erreur(s)\n"
                for result in results[:5]:  # Limiter à 5 exemples
                    report += f"     • {result.method} {result.endpoint} - {result.error_message}\n"
                if len(results) > 5:
                    report += f"     ... et {len(results)-5} autres\n"
            report += "\n"
            
        # Tests les plus lents
        slowest = sorted(self.results, key=lambda r: r.response_time, reverse=True)[:10]
        if slowest:
            report += "🐌 TESTS LES PLUS LENTS:\n"
            for result in slowest:
                status_icon = "✅" if result.success else "❌"
                report += f"   {status_icon} {result.method} {result.endpoint}: {result.response_time:.3f}s\n"
            report += "\n"
            
        # Recommandations
        report += "💡 RECOMMANDATIONS:\n"
        if failed_tests > 0:
            report += f"   • Corriger les {failed_tests} routes en échec\n"
        if avg_response_time > 2.0:
            report += "   • Optimiser les performances (temps de réponse > 2s)\n"
        if max_response_time > 5.0:
            report += "   • Investiguer les routes très lentes (> 5s)\n"
        if not self.authenticated:
            report += "   • Vérifier l'authentification pour tests complets\n"
            
        report += f"\n{'='*80}\n"
        return report
        
    def save_report(self, filename: str = None):
        """Sauvegarde le rapport dans un fichier"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tests/rapport_test_routes_{timestamp}.txt"
            
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
            
            # Ajouter les détails complets
            f.write("\n\n📋 DÉTAILS COMPLETS:\n")
            f.write("="*50 + "\n")
            
            for result in self.results:
                status_icon = "✅" if result.success else "❌"
                f.write(f"{status_icon} {result.method:6} {result.endpoint:40} "
                       f"{result.status_code:3} {result.response_time:6.3f}s")
                if result.description:
                    f.write(f" - {result.description}")
                if result.error_message:
                    f.write(f" | Erreur: {result.error_message}")
                f.write("\n")
                
        self.log(f"📄 Rapport sauvegardé: {filename}", Colors.GREEN)

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Test automatique des routes Flask')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='URL de base de l\'application')
    parser.add_argument('--auth-user', default='admin',
                       help='Nom d\'utilisateur pour l\'authentification')
    parser.add_argument('--auth-pass', default='admin123',
                       help='Mot de passe pour l\'authentification')
    parser.add_argument('--no-auth', action='store_true',
                       help='Exécuter les tests sans authentification')
    parser.add_argument('--report-file', 
                       help='Fichier de sortie pour le rapport')
    parser.add_argument('--quiet', action='store_true',
                       help='Affichage minimal')
    
    args = parser.parse_args()
    
    # Vérifier que l'application est accessible
    try:
        response = requests.get(args.url, timeout=10, verify=False)
        print(f"✅ Application accessible sur {args.url}")
    except Exception as e:
        print(f"❌ Impossible d'accéder à {args.url}: {e}")
        print("   Vérifiez que l'application Flask est démarrée.")
        sys.exit(1)
        
    # Créer et exécuter le testeur
    tester = RouteTester(args.url)
    
    if not args.quiet:
        tester.log("🧪 Testeur automatique de routes Flask démarré", Colors.BOLD + Colors.GREEN)
        
    # Exécuter les tests
    tester.run_all_tests(
        authenticate_first=not args.no_auth,
        username=args.auth_user,
        password=args.auth_pass
    )
    
    # Afficher et sauvegarder le rapport
    if not args.quiet:
        print(tester.generate_report())
        
    tester.save_report(args.report_file)
    
    # Code de sortie basé sur les résultats
    failed_tests = sum(1 for r in tester.results if not r.success)
    if failed_tests > 0:
        tester.log(f"❌ {failed_tests} test(s) en échec", Colors.RED)
        sys.exit(1)
    else:
        tester.log("✅ Tous les tests sont passés avec succès", Colors.GREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()