# Script PowerShell de Test Automatique - Régulation Électricité RDC
# ====================================================================
# 
# Usage:
#   .\run_tests.ps1
#   .\run_tests.ps1 -Quick
#   .\run_tests.ps1 -Url "http://localhost:8000"
#   .\run_tests.ps1 -SetupOnly

param(
    [string]$Url = "http://localhost:5000",
    [switch]$Quick = $false,
    [switch]$SetupOnly = $false,
    [switch]$Verbose = $false
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colors = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Magenta" = [ConsoleColor]::Magenta
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
    }
    
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Test-PythonModule {
    param([string]$ModuleName)
    
    try {
        python -c "import $ModuleName" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Test-AppRunning {
    param([string]$BaseUrl)
    
    try {
        $response = Invoke-WebRequest -Uri $BaseUrl -TimeoutSec 5 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Header
Write-ColorOutput "`n🧪 TESTS AUTOMATIQUES - REGULATION ELECTRICITE RDC" "Cyan"
Write-ColorOutput "====================================================" "Cyan"
Write-ColorOutput "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
Write-ColorOutput ""

# Vérification Python
Write-ColorOutput "🔍 Vérification de l'environnement..." "Blue"

try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput "✅ Python détecté: $pythonVersion" "Green"
}
catch {
    Write-ColorOutput "❌ Python n'est pas installé ou accessible" "Red"
    exit 1
}

# Vérification Flask
if (Test-PythonModule "flask") {
    Write-ColorOutput "✅ Flask disponible" "Green"
}
else {
    Write-ColorOutput "❌ Flask non disponible" "Red"
    Write-ColorOutput "Installation de Flask..." "Yellow"
    pip install flask
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Erreur installation Flask" "Red"
        exit 1
    }
}

# Installation des dépendances de test
$modules = @("requests", "bs4")
$needInstall = $false

foreach ($module in $modules) {
    if (-not (Test-PythonModule $module)) {
        $needInstall = $true
        break
    }
}

if ($needInstall) {
    Write-ColorOutput "📦 Installation des dépendances de test..." "Yellow"
    python tests/setup_test_env.py
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Erreur installation dépendances" "Red"
        exit 1
    }
}
Write-ColorOutput "✅ Dépendances de test disponibles" "Green"

# Si setup seulement, arrêter ici
if ($SetupOnly) {
    Write-ColorOutput "`n✅ Configuration terminée avec succès" "Green"
    exit 0
}

# Vérification de l'application Flask
Write-ColorOutput "`n🚀 Vérification de l'application Flask..." "Blue"

if (Test-AppRunning $Url) {
    Write-ColorOutput "✅ Application accessible sur $Url" "Green"
}
else {
    Write-ColorOutput "❌ Application non accessible sur $Url" "Red"
    Write-ColorOutput ""
    Write-ColorOutput "IMPORTANT: Vous devez démarrer l'application dans un autre terminal avec:" "Yellow"
    Write-ColorOutput "   flask --app run run --debug" "Cyan"
    Write-ColorOutput ""
    
    $response = Read-Host "Appuyez sur Entrée quand l'application est démarrée (ou 'q' pour quitter)"
    if ($response -eq 'q') {
        exit 1
    }
    
    # Revérifier
    if (-not (Test-AppRunning $Url)) {
        Write-ColorOutput "❌ Application toujours non accessible" "Red"
        Write-ColorOutput "Tests annulés" "Red"
        exit 1
    }
    Write-ColorOutput "✅ Application maintenant accessible" "Green"
}

# Exécution des tests
Write-ColorOutput "`n🧪 DÉBUT DES TESTS..." "Cyan"
Write-ColorOutput ""

$testArgs = @("tests/run_all_tests.py", "--url", $Url, "--full-report")

if ($Quick) {
    $testArgs += "--quick"
    Write-ColorOutput "⚡ Mode rapide activé" "Yellow"
}

if ($Verbose) {
    Write-ColorOutput "🔊 Mode verbose activé" "Yellow"
}

# Exécuter les tests
$startTime = Get-Date
python @testArgs

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-ColorOutput ""
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS" "Green"
}
else {
    Write-ColorOutput "⚠️ CERTAINS TESTS ONT ÉCHOUÉ" "Yellow"
    Write-ColorOutput "Consultez le rapport détaillé généré" "Yellow"
}

Write-ColorOutput "⏱️ Durée totale: $([math]::Round($duration, 1))s" "Blue"
Write-ColorOutput "📄 Rapports sauvegardés dans le dossier tests/" "Blue"

# Proposer d'ouvrir le rapport
$latestReport = Get-ChildItem -Path "tests/rapport_complet_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestReport) {
    $openReport = Read-Host "`nVoulez-vous ouvrir le dernier rapport généré ? (o/n)"
    if ($openReport -eq 'o' -or $openReport -eq 'O') {
        Start-Process notepad.exe -ArgumentList $latestReport.FullName
    }
}

# Résumé final
Write-ColorOutput "`n📊 RÉSUMÉ:" "Cyan"
Write-ColorOutput "  🎯 URL testée: $Url" "White"
Write-ColorOutput "  ⏱️ Durée: $([math]::Round($duration, 1))s" "White"
Write-ColorOutput "  📄 Rapport: $($latestReport.Name)" "White"

Write-ColorOutput "`n🏁 Tests terminés" "Green"