// Graphiques pour les données de distribution
document.addEventListener('DOMContentLoaded', function() {
    
    // Configuration des couleurs
    const colors = {
        primary: '#3498db',
        success: '#2ecc71',
        warning: '#f39c12',
        danger: '#e74c3c',
        info: '#17a2b8',
        purple: '#9b59b6'
    };

    // Graphique répartition des clients
    const clientsCtx = document.getElementById('clientsChart');
    if (clientsCtx) {
        try {
            const clientsData = JSON.parse(clientsCtx.dataset.clients || '{}');
            
            new Chart(clientsCtx, {
                type: 'doughnut',
                data: {
                    labels: ['HT', 'MT', 'BT'],
                    datasets: [{
                        data: [
                            clientsData.ht || 0,
                            clientsData.mt || 0,
                            clientsData.bt || 0
                        ],
                        backgroundColor: [colors.danger, colors.warning, colors.success],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Répartition des Clients par Tension',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erreur lors de la création du graphique clients:', e);
        }
    }

    // Graphique évolution mensuelle
    const evolutionCtx = document.getElementById('evolutionChart');
    if (evolutionCtx) {
        try {
            const evolutionData = JSON.parse(evolutionCtx.dataset.evolution || '[]');
            const labels = evolutionData.map(d => d.mois);
            const nouvelles = evolutionData.map(d => d.nouvelles_connexions || 0);
            const deconnexions = evolutionData.map(d => d.deconnexions || 0);
            
            new Chart(evolutionCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Nouvelles connexions',
                        data: nouvelles,
                        borderColor: colors.success,
                        backgroundColor: colors.success + '20',
                        tension: 0.4,
                        fill: true
                    }, {
                        label: 'Déconnexions',
                        data: deconnexions,
                        borderColor: colors.danger,
                        backgroundColor: colors.danger + '20',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Évolution Mensuelle des Connexions',
                            font: { size: 16, weight: 'bold' }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erreur lors de la création du graphique évolution:', e);
        }
    }

    // Graphique énergie
    const energieCtx = document.getElementById('energieChart');
    if (energieCtx) {
        try {
            const energieData = JSON.parse(energieCtx.dataset.energie || '{}');
            
            new Chart(energieCtx, {
                type: 'bar',
                data: {
                    labels: ['HT', 'MT', 'BT'],
                    datasets: [{
                        label: 'Énergie Distribuée (MWh)',
                        data: [
                            energieData.ht || 0,
                            energieData.mt || 0,
                            energieData.bt || 0
                        ],
                        backgroundColor: [colors.danger, colors.warning, colors.success],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribution par Niveau de Tension',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Énergie (MWh)'
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erreur lors de la création du graphique énergie:', e);
        }
    }

    // Graphique pertes
    const pertesCtx = document.getElementById('pertesChart');
    if (pertesCtx) {
        try {
            const pertesData = JSON.parse(pertesCtx.dataset.pertes || '{}');
            
            new Chart(pertesCtx, {
                type: 'pie',
                data: {
                    labels: ['Pertes Techniques', 'Pertes Commerciales'],
                    datasets: [{
                        data: [
                            pertesData.techniques || 0,
                            pertesData.commerciales || 0
                        ],
                        backgroundColor: [colors.warning, colors.danger],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Analyse des Pertes (MWh)',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erreur lors de la création du graphique pertes:', e);
        }
    }
});