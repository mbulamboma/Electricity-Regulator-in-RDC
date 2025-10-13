#!/usr/bin/env python3
"""
Script de Configuration pour les Tests
=====================================

Installe les dépendances nécessaires et configure l'environnement de test.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Installe les dépendances nécessaires pour les tests"""
    dependencies = [
        'requests',
        'beautifulsoup4',
        'lxml'  # Parser XML pour BeautifulSoup
    ]
    
    print("📦 Installation des dépendances pour les tests...")
    
    for dep in dependencies:
        try:
            print(f"  Installation de {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"  ✅ {dep} installé")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erreur installation {dep}: {e}")
            
def create_requirements_test():
    """Crée un fichier requirements-test.txt"""
    requirements_content = """# Dépendances pour les tests
requests>=2.25.1
beautifulsoup4>=4.9.3
lxml>=4.6.3

# Dépendances optionnelles pour tests avancés
selenium>=4.0.0  # Pour tests UI automatisés
pytest>=6.2.4   # Framework de test alternatif
pytest-flask>=1.2.0  # Extensions Flask pour pytest
"""
    
    with open('requirements-test.txt', 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print("📄 Fichier requirements-test.txt créé")
    
def main():
    """Fonction principale"""
    print("🔧 Configuration de l'environnement de test")
    print("="*50)
    
    create_requirements_test()
    install_dependencies()
    
    print("\n✅ Configuration terminée!")
    print("\n🚀 Vous pouvez maintenant exécuter:")
    print("   python tests/manual_test_routes.py")
    print("   python tests/test_forms.py")

if __name__ == "__main__":
    main()