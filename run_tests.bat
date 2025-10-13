@echo off
REM Script de Test Automatique - Régulation Électricité RDC
REM ========================================================
REM 
REM Ce script automatise complètement le processus de test :
REM 1. Vérifie l'environnement
REM 2. Installe les dépendances si nécessaire
REM 3. Démarre l'application Flask si elle n'est pas en cours
REM 4. Exécute tous les tests
REM 5. Génère le rapport
REM

echo.
echo 🧪 TESTS AUTOMATIQUES - REGULATION ELECTRICITE RDC
echo ====================================================
echo %date% %time%
echo.

REM Vérifier Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé ou accessible
    pause
    exit /b 1
)
echo ✅ Python détecté

REM Vérifier Flask
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flask n'est pas installé
    echo Installation de Flask...
    pip install flask
)
echo ✅ Flask disponible

REM Installer dépendances de test si nécessaire
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installation des dépendances de test...
    python tests/setup_test_env.py
    if %errorlevel% neq 0 (
        echo ❌ Erreur installation dépendances
        pause
        exit /b 1
    )
)
echo ✅ Dépendances de test disponibles

REM Vérifier si l'application est en cours d'exécution
python -c "import requests; requests.get('http://localhost:5000', timeout=2)" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🚀 L'application Flask n'est pas démarrée
    echo.
    echo IMPORTANT: Vous devez démarrer l'application dans un autre terminal avec:
    echo    flask --app run run --debug
    echo.
    echo Appuyez sur une touche quand l'application est démarrée...
    pause
    
    REM Revérifier
    python -c "import requests; requests.get('http://localhost:5000', timeout=2)" >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Application toujours non accessible
        echo Tests annulés
        pause
        exit /b 1
    )
)
echo ✅ Application Flask accessible

echo.
echo 🧪 DÉBUT DES TESTS...
echo.

REM Exécuter les tests complets
python tests/run_all_tests.py --full-report

if %errorlevel% equ 0 (
    echo.
    echo ✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS
    echo.
) else (
    echo.
    echo ⚠️ CERTAINS TESTS ONT ÉCHOUÉ
    echo Consultez le rapport détaillé généré
    echo.
)

echo 📄 Rapports sauvegardés dans le dossier tests/
echo.

REM Proposer d'ouvrir le rapport
set /p choice="Voulez-vous ouvrir le dernier rapport généré ? (o/n): "
if /i "%choice%"=="o" (
    for /f "delims=" %%f in ('dir tests\rapport_complet_*.txt /b /od 2^>nul ^| tail -1') do (
        if exist "tests\%%f" (
            notepad "tests\%%f"
        )
    )
)

echo.
echo 🏁 Tests terminés
pause