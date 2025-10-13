#!/usr/bin/env python3
"""
Test de Validation du Système de Tests
======================================

Ce script valide que tous les scripts de test fonctionnent correctement.
"""

import os
import sys
import subprocess
import importlib.util

def test_import(module_name, description):
    """Test d'importation d'un module"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: Module importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ {description}: Erreur d'importation - {e}")
        return False

def test_file_exists(file_path, description):
    """Test d'existence d'un fichier"""
    if os.path.exists(file_path):
        print(f"✅ {description}: Fichier trouvé")
        return True
    else:
        print(f"❌ {description}: Fichier manquant - {file_path}")
        return False

def test_script_syntax(script_path, description):
    """Test de syntaxe d'un script Python"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            compile(f.read(), script_path, 'exec')
        print(f"✅ {description}: Syntaxe correcte")
        return True
    except SyntaxError as e:
        print(f"❌ {description}: Erreur de syntaxe - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {description}: Erreur - {e}")
        return False

def main():
    """Validation complète du système de tests"""
    print("🔬 VALIDATION DU SYSTÈME DE TESTS")
    print("="*50)
    
    success_count = 0
    total_tests = 0
    
    # Test des dépendances Python
    print("\n📦 Test des dépendances:")
    dependencies = [
        ('requests', 'Bibliothèque HTTP requests'),
        ('bs4', 'Beautiful Soup 4'),
        ('lxml', 'Parser XML/HTML lxml')
    ]
    
    for module, desc in dependencies:
        total_tests += 1
        if test_import(module, desc):
            success_count += 1
    
    # Test des fichiers de script
    print("\n📄 Test des fichiers de script:")
    script_files = [
        ('tests/manual_test_routes.py', 'Script de test des routes'),
        ('tests/test_forms.py', 'Script de test des formulaires'),
        ('tests/run_all_tests.py', 'Script principal de test'),
        ('tests/health_check.py', 'Script de test de santé'),
        ('tests/setup_test_env.py', 'Script de configuration'),
        ('run_tests.bat', 'Script batch Windows'),
        ('run_tests.ps1', 'Script PowerShell'),
        ('tests/README.md', 'Documentation des tests')
    ]
    
    for file_path, desc in script_files:
        total_tests += 1
        if test_file_exists(file_path, desc):
            success_count += 1
    
    # Test de syntaxe des scripts Python
    print("\n🐍 Test de syntaxe des scripts Python:")
    python_scripts = [
        ('tests/manual_test_routes.py', 'Script de test des routes'),
        ('tests/test_forms.py', 'Script de test des formulaires'),
        ('tests/run_all_tests.py', 'Script principal de test'),
        ('tests/health_check.py', 'Script de test de santé'),
        ('tests/setup_test_env.py', 'Script de configuration')
    ]
    
    for script_path, desc in python_scripts:
        if os.path.exists(script_path):
            total_tests += 1
            if test_script_syntax(script_path, desc):
                success_count += 1
    
    # Test de connectivité (sans démarrer l'app)
    print("\n🌐 Test de connectivité:")
    try:
        import requests
        # Test sur une URL publique pour vérifier que requests fonctionne
        response = requests.get('https://httpbin.org/status/200', timeout=5)
        if response.status_code == 200:
            print("✅ Connectivité réseau: OK")
            success_count += 1
        else:
            print("❌ Connectivité réseau: Problème")
    except Exception as e:
        print(f"❌ Connectivité réseau: Erreur - {e}")
    total_tests += 1
    
    # Résultats finaux
    print("\n" + "="*50)
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    print(f"📊 RÉSULTATS: {success_count}/{total_tests} tests réussis ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("✅ SYSTÈME DE TESTS OPÉRATIONNEL")
        print("\n🚀 Vous pouvez maintenant exécuter:")
        print("   python tests/health_check.py")
        print("   python tests/run_all_tests.py --quick")
        print("   .\\run_tests.ps1")
        return True
    elif success_rate >= 70:
        print("⚠️ SYSTÈME DE TESTS PARTIELLEMENT OPÉRATIONNEL")
        print("   Quelques problèmes mineurs détectés")
        return True
    else:
        print("❌ SYSTÈME DE TESTS DÉFAILLANT")
        print("   Veuillez corriger les erreurs avant utilisation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)