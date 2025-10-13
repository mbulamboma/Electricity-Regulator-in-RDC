/**
 * Dashboard ARE - Scripts JavaScript
 * Gestion des widgets interactifs et mise à jour automatique
 */

class DashboardARE {
    constructor() {
        this.charts = {};
        this.autoRefreshInterval = null;
        this.isAutoRefreshEnabled = false;
        this.data = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    initWithData(data) {
        this.data = data;
        this.initializeCharts();
    }

    initializeCharts() {
        // Graphique mix énergétique
        this.initMixEnergetiqueChart();
        
        // Graphiques de performance
        this.initPerformanceCharts();
        
        // Graphiques d'évolution temporelle
        this.initEvolutionChart();
    }

    initMixEnergetiqueChart() {
        const ctx = document.getElementById('mixEnergetiqueChart');
        if (!ctx) return;

        // Utiliser les données du template si disponibles
        const mixData = this.data?.mixEnergetique || { hydro: 0, thermique: 0, solaire: 0 };

        this.charts.mixEnergetique = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Hydraulique', 'Thermique', 'Solaire', 'Autres'],
                datasets: [{
                    data: [
                        mixData.hydro || 0,
                        mixData.thermique || 0,
                        mixData.solaire || 0,
                        Math.max(0, 100 - (mixData.hydro + mixData.thermique + mixData.solaire))
                    ],
                    backgroundColor: [
                        '#17a2b8',
                        '#ffc107',
                        '#28a745',
                        '#6c757d'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
    }

    initPerformanceCharts() {
        // Graphique en barres pour la performance des opérateurs
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Production (MWh)',
                    data: [],
                    backgroundColor: '#007bff',
                    borderColor: '#0056b3',
                    borderWidth: 1
                }, {
                    label: 'Facteur de charge (%)',
                    data: [],
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Production (MWh)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Facteur de charge (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    initEvolutionChart() {
        // Graphique d'évolution temporelle des KPIs
        const ctx = document.getElementById('evolutionChart');
        if (!ctx) return;

        this.charts.evolution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Période'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Valeur'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    setupEventListeners() {
        // Filtres du dashboard
        const filtreForm = document.querySelector('#filtreForm');
        if (filtreForm) {
            filtreForm.addEventListener('submit', (e) => {
                this.onFiltreSubmit(e);
            });
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.querySelector('#autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.toggleAutoRefresh(e.target.checked);
            });
        }

        // Export buttons
        const exportButtons = document.querySelectorAll('.btn-export');
        exportButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleExport(e);
            });
        });

        // Actualisation manuelle
        const refreshBtn = document.querySelector('#refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllData();
            });
        }
    }

    onFiltreSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const params = new URLSearchParams(formData);
        
        // Mettre à jour l'URL sans recharger la page
        const newUrl = window.location.pathname + '?' + params.toString();
        window.history.pushState({}, '', newUrl);
        
        // Actualiser les données
        this.refreshAllData();
    }

    toggleAutoRefresh(enabled) {
        this.isAutoRefreshEnabled = enabled;
        
        if (enabled) {
            this.startAutoRefresh();
            this.showNotification('Actualisation automatique activée (5 min)', 'success');
        } else {
            this.stopAutoRefresh();
            this.showNotification('Actualisation automatique désactivée', 'info');
        }
    }

    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        // Actualisation toutes les 5 minutes
        this.autoRefreshInterval = setInterval(() => {
            if (this.isAutoRefreshEnabled) {
                this.refreshAllData();
            }
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    async refreshAllData() {
        try {
            this.showLoading(true);
            
            const annee = this.data?.annee || new Date().getFullYear();
            const operateurId = this.data?.operateurId;
            
            // Actualiser le mix énergétique
            await this.updateMixEnergetique(annee, operateurId);
            
            // Actualiser les KPIs
            await this.updateKPIs(annee, operateurId);
            
            // Actualiser la performance des opérateurs
            await this.updatePerformanceOperateurs(annee, operateurId);
            
            this.showNotification('Données actualisées', 'success');
            
        } catch (error) {
            console.error('Erreur actualisation:', error);
            this.showNotification('Erreur lors de l\'actualisation', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async updateMixEnergetique(annee, operateurId) {
        const url = `/are/dashboard/api/mix-energetique/${annee}${operateurId ? '?operateur_id=' + operateurId : ''}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (this.charts.mixEnergetique) {
            const total = data.total || 1;
            const pourcentages = [
                data.hydro || 0,
                data.thermique || 0,
                data.solaire || 0,
                Math.max(0, 100 - (data.hydro + data.thermique + data.solaire))
            ];
            
            this.charts.mixEnergetique.data.datasets[0].data = pourcentages;
            this.charts.mixEnergetique.update('active');
            
            // Mettre à jour les statistiques textuelles
            this.updateMixStats(data);
        }
    }

    updateMixStats(data) {
        const statsContainer = document.querySelector('#mixStats');
        if (!statsContainer) return;
        
        statsContainer.innerHTML = `
            <div class="row text-center">
                <div class="col-4">
                    <div class="h5 text-info">${data.hydro.toFixed(1)}%</div>
                    <small class="text-muted">Hydraulique</small>
                </div>
                <div class="col-4">
                    <div class="h5 text-warning">${data.thermique.toFixed(1)}%</div>
                    <small class="text-muted">Thermique</small>
                </div>
                <div class="col-4">
                    <div class="h5 text-success">${data.solaire.toFixed(1)}%</div>
                    <small class="text-muted">Solaire</small>
                </div>
            </div>
        `;
    }

    async updateKPIs(annee, operateurId) {
        const url = `/are/dashboard/api/kpis/${annee}${operateurId ? '?operateur_id=' + operateurId : ''}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Mettre à jour les cartes KPIs
        const kpiContainer = document.querySelector('#kpiContainer');
        if (kpiContainer && data.kpis) {
            this.renderKPICards(data.kpis, kpiContainer);
        }
    }

    renderKPICards(kpis, container) {
        container.innerHTML = '';
        
        kpis.slice(0, 6).forEach(kpi => {
            const card = document.createElement('div');
            card.className = 'col-md-6 mb-3';
            
            const tendanceIcon = this.getTendanceIcon(kpi.tendance);
            const alerteClass = kpi.seuil_alerte && kpi.valeur < kpi.seuil_alerte ? 'border-danger' : '';
            
            card.innerHTML = `
                <div class="border rounded p-3 ${alerteClass}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${kpi.nom}</h6>
                            <div class="h4 mb-1 text-primary">
                                ${this.formatNumber(kpi.valeur)} ${kpi.unite}
                            </div>
                            ${kpi.objectif ? `<small class="text-muted">Objectif: ${this.formatNumber(kpi.objectif)} ${kpi.unite}</small>` : ''}
                        </div>
                        <div class="text-end">
                            ${tendanceIcon}
                        </div>
                    </div>
                    ${kpi.seuil_alerte && kpi.valeur < kpi.seuil_alerte ? 
                        '<div class="mt-2"><small class="text-danger"><i class="fas fa-exclamation-triangle"></i> Seuil d\'alerte atteint</small></div>' : ''}
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    getTendanceIcon(tendance) {
        if (!tendance) return '';
        
        switch (tendance) {
            case 'hausse':
                return '<i class="fas fa-arrow-up text-success"></i>';
            case 'baisse':
                return '<i class="fas fa-arrow-down text-danger"></i>';
            default:
                return '<i class="fas fa-minus text-warning"></i>';
        }
    }

    async updatePerformanceOperateurs(annee, operateurId) {
        // Si un opérateur spécifique est sélectionné, pas besoin du graphique comparatif
        if (operateurId) return;
        
        try {
            const response = await fetch(`/are/dashboard/api/performance-operateurs/${annee}`);
            const data = await response.json();
            
            if (this.charts.performance && data.performance) {
                const operateurs = data.performance.slice(0, 10); // Top 10
                
                this.charts.performance.data.labels = operateurs.map(op => op.operateur);
                this.charts.performance.data.datasets[0].data = operateurs.map(op => op.production_annuelle);
                this.charts.performance.data.datasets[1].data = operateurs.map(op => op.facteur_charge);
                
                this.charts.performance.update('active');
            }
        } catch (error) {
            console.error('Erreur mise à jour performance:', error);
        }
    }

    handleExport(e) {
        const format = e.target.dataset.format;
        const type = e.target.dataset.type || 'dashboard';
        
        this.showLoading(true);
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/are/dashboard/export';
        
        // Ajouter les paramètres actuels
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.forEach((value, key) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            form.appendChild(input);
        });
        
        // Ajouter le format d'export
        const formatInput = document.createElement('input');
        formatInput.type = 'hidden';
        formatInput.name = 'format';
        formatInput.value = format;
        form.appendChild(formatInput);
        
        // Ajouter le token CSRF
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = document.querySelector('meta[name=csrf-token]').getAttribute('content');
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
        setTimeout(() => this.showLoading(false), 2000);
    }

    formatNumber(value) {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
        }
        return value.toFixed(1);
    }

    showLoading(show) {
        const loader = document.querySelector('#dashboardLoader');
        if (loader) {
            loader.style.display = show ? 'block' : 'none';
        }
        
        // Désactiver/activer les boutons
        const buttons = document.querySelectorAll('.btn-dashboard-action');
        buttons.forEach(btn => {
            btn.disabled = show;
        });
    }

    showNotification(message, type = 'info') {
        const alertClass = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type] || 'alert-info';
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    // Méthode pour initialiser la carte RDC interactive
    initCarteRDC() {
        const carteContainer = document.querySelector('#carteRDC');
        if (!carteContainer) return;
        
        // Ici on peut implémenter une carte SVG interactive
        // ou utiliser une bibliothèque comme D3.js ou Leaflet
        
        // Pour l'instant, simulation avec zones cliquables
        carteContainer.addEventListener('click', (e) => {
            const rect = carteContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Définir des zones approximatives pour chaque province
            const provinces = this.getProvinceFromCoordinates(x, y);
            if (provinces) {
                this.showProvinceDetails(provinces);
            }
        });
    }

    getProvinceFromCoordinates(x, y) {
        // Mapping approximatif des coordonnées vers les provinces
        // À adapter selon la vraie carte SVG de la RDC
        const carteWidth = 400;
        const carteHeight = 400;
        
        if (x < carteWidth * 0.3 && y > carteHeight * 0.7) {
            return 'Bas-Congo';
        } else if (x < carteWidth * 0.4 && y > carteHeight * 0.5 && y < carteHeight * 0.7) {
            return 'Kinshasa';
        } else if (x > carteWidth * 0.6 && y < carteHeight * 0.3) {
            return 'Orientale';
        }
        // ... autres provinces
        
        return null;
    }

    showProvinceDetails(province) {
        // Afficher les détails de la province dans un modal ou tooltip
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Province de ${province}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Chargement des données de ${province}...</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Charger les données de la province
        this.loadProvinceData(province, modal.querySelector('.modal-body'));
        
        // Nettoyer après fermeture
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async loadProvinceData(province, container) {
        try {
            const response = await fetch(`/are/dashboard/api/province/${province}`);
            const data = await response.json();
            
            container.innerHTML = `
                <div class="row">
                    <div class="col-6">
                        <strong>Taux d'accès électricité:</strong><br>
                        <span class="h5 text-primary">${data.taux_acces || 0}%</span>
                    </div>
                    <div class="col-6">
                        <strong>Puissance installée:</strong><br>
                        <span class="h5 text-success">${data.puissance_installee || 0} MW</span>
                    </div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-6">
                        <strong>Population:</strong><br>
                        ${this.formatNumber(data.population || 0)}
                    </div>
                    <div class="col-6">
                        <strong>Opérateurs actifs:</strong><br>
                        ${data.nombre_operateurs || 0}
                    </div>
                </div>
            `;
        } catch (error) {
            container.innerHTML = '<p class="text-danger">Erreur lors du chargement des données.</p>';
        }
    }
}

// Initialisation du dashboard
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardARE = new DashboardARE();
});