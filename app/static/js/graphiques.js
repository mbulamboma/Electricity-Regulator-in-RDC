/**
 * Gestionnaire de graphiques réutilisables
 * Utilise Chart.js pour créer des graphiques à partir de configurations JSON
 */

// Variables globales
window.chartInstances = window.chartInstances || {};

/**
 * Initialiser tous les graphiques au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Graphiques principaux
    initAllCharts();
    
    // Graphiques de jauges
    initAllGauges();
    
    // Mini graphiques
    initAllMiniCharts();
});

/**
 * Initialiser tous les graphiques Chart.js
 */
function initAllCharts() {
    // Rechercher tous les éléments de configuration
    const configElements = document.querySelectorAll('script[type="application/json"][id$="-config"]');
    
    configElements.forEach(configElement => {
        const chartId = configElement.id.replace('-config', '');
        const canvas = document.getElementById(chartId);
        
        if (canvas && configElement.textContent) {
            try {
                const config = JSON.parse(configElement.textContent);
                
                // Traitement spécial pour les callbacks de tooltip
                if (config.options && config.options.plugins && config.options.plugins.tooltip && config.options.plugins.tooltip.callbacks) {
                    const callbacks = config.options.plugins.tooltip.callbacks;
                    if (typeof callbacks.label === 'string') {
                        // Évaluer la fonction JavaScript depuis la chaîne
                        config.options.plugins.tooltip.callbacks.label = new Function('context', callbacks.label.replace('function(context) { ', '').replace(' }', ''));
                    }
                }
                
                // Créer le graphique
                const chart = new Chart(canvas, config);
                window.chartInstances[chartId] = chart;
                
            } catch (error) {
                console.error(`Erreur lors de l'initialisation du graphique ${chartId}:`, error);
            }
        }
    });
}

/**
 * Initialiser tous les graphiques de jauges
 */
function initAllGauges() {
    const gaugeElements = document.querySelectorAll('script[type="application/json"][id$="-gauge-data"]');
    
    gaugeElements.forEach(gaugeElement => {
        const gaugeId = gaugeElement.id.replace('-gauge-data', '');
        const canvas = document.getElementById(gaugeId);
        
        if (canvas && gaugeElement.textContent) {
            try {
                const data = JSON.parse(gaugeElement.textContent);
                drawGauge(canvas, data);
            } catch (error) {
                console.error(`Erreur lors de l'initialisation de la jauge ${gaugeId}:`, error);
            }
        }
    });
}

/**
 * Initialiser tous les mini graphiques
 */
function initAllMiniCharts() {
    const miniConfigElements = document.querySelectorAll('script[type="application/json"][id$="-mini-config"]');
    
    miniConfigElements.forEach(configElement => {
        const chartId = configElement.id.replace('-mini-config', '');
        const canvas = document.getElementById(chartId);
        
        if (canvas && configElement.textContent) {
            try {
                const config = JSON.parse(configElement.textContent);
                const chart = new Chart(canvas, config);
                window.chartInstances[chartId] = chart;
            } catch (error) {
                console.error(`Erreur lors de l'initialisation du mini graphique ${chartId}:`, error);
            }
        }
    });
}

/**
 * Dessiner une jauge personnalisée
 */
function drawGauge(canvas, data) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height - 20;
    const radius = 80;
    
    // Calculer l'angle basé sur la valeur
    const percentage = data.valeur / data.max_value;
    const angle = Math.PI * percentage;
    
    // Effacer le canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Dessiner le fond de la jauge
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
    ctx.lineWidth = 15;
    ctx.strokeStyle = '#e9ecef';
    ctx.stroke();
    
    // Dessiner la jauge
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, Math.PI + angle);
    ctx.lineWidth = 15;
    
    // Couleur basée sur la valeur
    let strokeColor = '#28a745'; // Vert par défaut
    
    if (data.options.color_ranges && data.options.color_ranges.length > 0) {
        data.options.color_ranges.forEach(range => {
            if (percentage >= range.min / 100 && percentage <= range.max / 100) {
                strokeColor = range.color;
            }
        });
    } else {
        if (percentage < 0.5) {
            strokeColor = '#dc3545'; // Rouge
        } else if (percentage < 0.8) {
            strokeColor = '#ffc107'; // Jaune
        } else {
            strokeColor = '#28a745'; // Vert
        }
    }
    
    ctx.strokeStyle = strokeColor;
    ctx.stroke();
    
    // Dessiner les graduations
    ctx.strokeStyle = '#6c757d';
    ctx.lineWidth = 2;
    
    for (let i = 0; i <= 10; i++) {
        const tickAngle = Math.PI + (Math.PI * i / 10);
        const innerRadius = radius - 10;
        const outerRadius = radius + 5;
        
        const x1 = centerX + Math.cos(tickAngle) * innerRadius;
        const y1 = centerY + Math.sin(tickAngle) * innerRadius;
        const x2 = centerX + Math.cos(tickAngle) * outerRadius;
        const y2 = centerY + Math.sin(tickAngle) * outerRadius;
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }
    
    // Dessiner les étiquettes de valeurs
    ctx.fillStyle = '#6c757d';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    
    // Valeur minimale (0)
    ctx.fillText('0', centerX - radius + 10, centerY + 15);
    
    // Valeur maximale
    ctx.fillText(data.max_value.toString(), centerX + radius - 10, centerY + 15);
    
    // Valeur médiane
    const medianValue = Math.round(data.max_value / 2);
    ctx.fillText(medianValue.toString(), centerX, centerY - radius + 25);
}

/**
 * Télécharger un graphique
 */
function telechargerGraphique(chartId, format = 'png') {
    const canvas = document.getElementById(chartId);
    if (canvas) {
        const url = canvas.toDataURL(`image/${format}`);
        const link = document.createElement('a');
        link.download = `graphique_${chartId}_${new Date().toISOString().split('T')[0]}.${format}`;
        link.href = url;
        link.click();
    }
}

/**
 * Basculer en plein écran
 */
function basculerPleinEcran(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!document.fullscreenElement) {
        container.requestFullscreen().then(() => {
            container.classList.add('fullscreen-chart');
            
            // Redimensionner le graphique après un délai
            setTimeout(() => {
                const canvas = container.querySelector('canvas');
                if (canvas) {
                    const chartId = canvas.id;
                    const chart = window.chartInstances[chartId];
                    if (chart) {
                        chart.resize();
                    }
                }
            }, 100);
        }).catch(err => {
            console.log('Erreur plein écran:', err);
        });
    } else {
        document.exitFullscreen().then(() => {
            container.classList.remove('fullscreen-chart');
            
            // Redimensionner le graphique après sortie du plein écran
            setTimeout(() => {
                const canvas = container.querySelector('canvas');
                if (canvas) {
                    const chartId = canvas.id;
                    const chart = window.chartInstances[chartId];
                    if (chart) {
                        chart.resize();
                    }
                }
            }, 100);
        });
    }
}

/**
 * Mettre à jour un graphique existant
 */
function mettreAJourGraphique(chartId, nouvellesDonnees, nouvellesOptions = null) {
    const chart = window.chartInstances[chartId];
    if (chart) {
        // Mettre à jour les données
        if (nouvellesDonnees.labels) {
            chart.data.labels = nouvellesDonnees.labels;
        }
        
        if (nouvellesDonnees.datasets) {
            chart.data.datasets = nouvellesDonnees.datasets;
        }
        
        // Mettre à jour les options si fournies
        if (nouvellesOptions) {
            Object.assign(chart.options, nouvellesOptions);
        }
        
        // Redessiner le graphique
        chart.update();
    }
}

/**
 * Détruire un graphique
 */
function detruireGraphique(chartId) {
    const chart = window.chartInstances[chartId];
    if (chart) {
        chart.destroy();
        delete window.chartInstances[chartId];
    }
}

/**
 * Redimensionner tous les graphiques
 */
function redimensionnerTousLesGraphiques() {
    Object.values(window.chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

/**
 * Gestionnaire de redimensionnement de fenêtre
 */
window.addEventListener('resize', function() {
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(() => {
        redimensionnerTousLesGraphiques();
    }, 250);
});

/**
 * Gestionnaire de changement de plein écran
 */
document.addEventListener('fullscreenchange', function() {
    setTimeout(() => {
        redimensionnerTousLesGraphiques();
    }, 100);
});

/**
 * Couleurs prédéfinies pour les graphiques
 */
const COULEURS_GRAPHIQUES = {
    primaire: '#007bff',
    secondaire: '#6c757d',
    succes: '#28a745',
    danger: '#dc3545',
    avertissement: '#ffc107',
    info: '#17a2b8',
    clair: '#f8f9fa',
    sombre: '#343a40'
};

const PALETTES_COULEURS = {
    defaut: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
    pastel: ['#FFB6C1', '#87CEEB', '#DDA0DD', '#98FB98', '#F0E68C', '#FFA07A'],
    vive: ['#FF4500', '#32CD32', '#FF1493', '#00CED1', '#FFD700', '#8A2BE2'],
    professionnelle: ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3D1A78', '#4F5902']
};

/**
 * Obtenir une couleur de la palette
 */
function obtenirCouleur(index, palette = 'defaut') {
    const couleurs = PALETTES_COULEURS[palette] || PALETTES_COULEURS.defaut;
    return couleurs[index % couleurs.length];
}

/**
 * Générer des couleurs dégradées
 */
function genererDegrade(couleurBase, nombre) {
    const couleurs = [];
    const base = hexVersRgb(couleurBase);
    
    for (let i = 0; i < nombre; i++) {
        const facteur = 0.8 + (0.4 * i / nombre);
        const r = Math.round(base.r * facteur);
        const g = Math.round(base.g * facteur);
        const b = Math.round(base.b * facteur);
        couleurs.push(`rgb(${r}, ${g}, ${b})`);
    }
    
    return couleurs;
}

/**
 * Convertir hex en RGB
 */
function hexVersRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}

/**
 * Créer un graphique dynamiquement
 */
function creerGraphiqueDynamique(containerId, config) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} introuvable`);
        return null;
    }
    
    // Créer le canvas
    const canvas = document.createElement('canvas');
    canvas.id = `${containerId}-chart`;
    canvas.width = 400;
    canvas.height = 300;
    
    // Ajouter le canvas au container
    container.appendChild(canvas);
    
    // Créer le graphique
    const chart = new Chart(canvas, config);
    window.chartInstances[canvas.id] = chart;
    
    return chart;
}

/**
 * Animer la mise à jour d'un graphique
 */
function animerMiseAJourGraphique(chartId, nouvellesDonnees, duree = 1000) {
    const chart = window.chartInstances[chartId];
    if (!chart) return;
    
    // Configuration de l'animation
    chart.options.animation = {
        duration: duree,
        easing: 'easeInOutQuart'
    };
    
    // Mettre à jour les données
    mettreAJourGraphique(chartId, nouvellesDonnees);
}

/**
 * Exporter les données d'un graphique vers CSV
 */
function exporterGraphiqueCSV(chartId) {
    const chart = window.chartInstances[chartId];
    if (!chart) return;
    
    const data = chart.data;
    let csv = 'Label';
    
    // En-têtes des datasets
    data.datasets.forEach(dataset => {
        csv += `,${dataset.label || 'Dataset'}`;
    });
    csv += '\n';
    
    // Données
    data.labels.forEach((label, index) => {
        csv += `${label}`;
        data.datasets.forEach(dataset => {
            csv += `,${dataset.data[index] || ''}`;
        });
        csv += '\n';
    });
    
    // Télécharger le fichier
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `donnees_${chartId}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
}