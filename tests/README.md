# Scripts de Test Automatisé - Régulation Électricité RDC

## 📋 Vue d'ensemble

Cette suite de scripts permet de tester automatiquement toutes les routes et fonctionnalités de l'application Flask comme le ferait un utilisateur humain. Elle identifie les erreurs, mesure les performances et génère des rapports détaillés.

## 🚀 Installation et Configuration

### 1. Installation des dépendances

```powershell
# Installer les dépendances de test
python tests/setup_test_env.py

# Ou manuellement
pip install requests beautifulsoup4 lxml
```

### 2. Démarrer l'application Flask

```powershell
# Dans un terminal séparé
flask --app run run --debug
```

L'application doit être accessible sur `http://localhost:5000`

## 🧪 Scripts de Test Disponibles

### 1. Tests Complets (Recommandé)

```powershell
# Tests complets avec rapport détaillé
python tests/run_all_tests.py --full-report

# Tests rapides (routes principales seulement)
python tests/run_all_tests.py --quick

# Tests sur une URL personnalisée
python tests/run_all_tests.py --url http://localhost:8000
```

### 2. Tests de Routes Spécifiques

```powershell
# Tester toutes les routes
python tests/manual_test_routes.py

# Tests avec authentification personnalisée
python tests/manual_test_routes.py --auth-user admin --auth-pass admin123

# Tests sans authentification
python tests/manual_test_routes.py --no-auth

# Rapport silencieux
python tests/manual_test_routes.py --quiet --report-file rapport_custom.txt
```

### 3. Tests de Formulaires

```powershell
# Tester tous les formulaires avec validation
python tests/test_forms.py

# Tests sur URL personnalisée
python tests/test_forms.py http://localhost:8000
```

## 📊 Types de Tests Effectués

### 🔗 Tests de Routes

- **Routes d'authentification** : Login, logout, register
- **Routes opérateurs** : CRUD complet des opérateurs
- **Routes production** : Hydro, thermique, solaire
- **Routes transport** : Lignes de transport électrique
- **Routes distribution** : Réseaux et postes de distribution
- **Routes workflow** : Gestion des workflows et validations
- **Routes notifications** : Système de notifications
- **Routes contacts** : Gestion des contacts
- **Routes admin** : Administration et gestion utilisateurs
- **Routes ARE** : Dashboard et KPIs de régulation
- **Routes d'erreur** : Test des codes d'erreur 404, etc.

### 📝 Tests de Formulaires

- **Validation des données** : Test avec données valides et invalides
- **Tokens CSRF** : Vérification de la sécurité CSRF
- **Messages d'erreur** : Affichage correct des erreurs de validation
- **Redirection** : Comportement après soumission réussie

### 🗄️ Tests de Base de Données

- **Connexion** : Vérification de l'accès à la base
- **Requêtes basiques** : Comptage des entités principales
- **Intégrité** : Vérification de la cohérence des données

## 📈 Rapports Générés

### Structure du Rapport

```
📊 RAPPORT CONSOLIDÉ DE TESTS
================================

🎯 APPLICATION TESTÉE: http://localhost:5000

🔗 TESTS DE ROUTES:
   Total: 85 routes testées
   ✅ Succès: 78 (91.8%)
   ❌ Échecs: 7
   ⏱️ Temps d'exécution: 12.3s

📝 TESTS DE FORMULAIRES:
   ✅ Statut: completed
   ⏱️ Temps d'exécution: 8.7s

🗄️ TESTS DE BASE DE DONNÉES:
   ✅ Statut: success
   👥 Utilisateurs: 3
   🏢 Opérateurs: 5
   ⏱️ Temps d'exécution: 0.2s

💡 RECOMMANDATIONS:
   • Corriger 7 route(s) en échec
   • Exécuter les tests régulièrement
```

### Fichiers de Rapport

Les rapports sont automatiquement sauvegardés dans :
- `tests/rapport_complet_YYYYMMDD_HHMMSS.txt`
- `tests/rapport_test_routes_YYYYMMDD_HHMMSS.txt`

## 🔧 Configuration Avancée

### Variables d'Environnement

```powershell
# URL de base personnalisée
$env:TEST_BASE_URL = "http://localhost:8000"

# Credentials de test
$env:TEST_USER = "admin"
$env:TEST_PASS = "password123"
```

### Personnalisation des Tests

Vous pouvez modifier les scripts pour :
- Ajouter de nouvelles routes à tester
- Changer les données de test
- Modifier les critères de validation
- Ajouter des métriques personnalisées

## 🚨 Dépannage

### Problèmes Courants

1. **Application non accessible**
   ```
   ❌ Impossible d'accéder à http://localhost:5000
   ```
   **Solution** : Vérifiez que Flask est démarré avec `flask --app run run --debug`

2. **Erreurs d'importation**
   ```
   Import "requests" could not be resolved
   ```
   **Solution** : Installez les dépendances avec `python tests/setup_test_env.py`

3. **Erreurs d'authentification**
   ```
   ❌ Échec authentification: 401
   ```
   **Solution** : Vérifiez les credentials par défaut (`admin`/`admin123`)

4. **Erreurs CSRF**
   ```
   CSRF token missing or incorrect
   ```
   **Solution** : Les scripts gèrent automatiquement CSRF, vérifiez que les formulaires ont le bon format

### Mode Debug

Pour plus de détails sur les erreurs :

```powershell
# Activer le mode verbose
python tests/manual_test_routes.py --no-quiet

# Voir les détails complets
python tests/run_all_tests.py --full-report
```

## 📅 Intégration Continue

### Exécution Automatique

Créez un script batch pour l'exécution régulière :

```batch
@echo off
echo Tests automatiques - %date% %time%
python tests/run_all_tests.py --quick
if %errorlevel% neq 0 (
    echo ECHEC DES TESTS
    exit /b 1
)
echo TESTS REUSSIS
```

### Surveillance Continue

```powershell
# Tests toutes les 30 minutes
while ($true) {
    python tests/run_all_tests.py --quick
    Start-Sleep 1800
}
```

## 🎯 Métriques et KPIs

Les scripts mesurent automatiquement :
- **Temps de réponse** moyen/min/max
- **Taux de succès** par type de route
- **Performance** de la base de données
- **Couverture** des tests de formulaires

## 🔄 Mise à Jour

Pour maintenir les scripts à jour :
1. Ajoutez nouvelles routes dans `manual_test_routes.py`
2. Ajoutez nouveaux formulaires dans `test_forms.py`
3. Mettez à jour les données de test selon l'évolution de l'application

## 📞 Support

Pour signaler des problèmes ou suggestions d'amélioration :
1. Vérifiez les logs de test générés
2. Consultez la section Dépannage
3. Documentez l'erreur avec le rapport complet