/**
 * Utilitaires pour la gestion dynamique des transformateurs
 * Transport et Distribution
 */

// Variables globales
let compteurTransformateurs = 0;

/**
 * Ajouter un nouveau transformateur
 */
function ajouterTransformateur(type = 'transport') {
    compteurTransformateurs++;
    
    const container = document.getElementById('transformateurs-container');
    const template = document.getElementById('transformateur-template');
    
    if (!container || !template) {
        console.error('Container ou template transformateur non trouvé');
        return;
    }
    
    // Cloner le template
    const nouveauTransformateur = template.cloneNode(true);
    nouveauTransformateur.id = `transformateur-${compteurTransformateurs}`;
    nouveauTransformateur.style.display = 'block';
    
    // Mettre à jour les noms des champs
    const champs = nouveauTransformateur.querySelectorAll('input, select, textarea');
    champs.forEach(champ => {
        if (champ.name) {
            // Remplacer [0] par [compteur] dans le nom
            champ.name = champ.name.replace('[0]', `[${compteurTransformateurs}]`);
            champ.id = champ.id.replace('_0_', `_${compteurTransformateurs}_`);
        }
    });
    
    // Mettre à jour les labels
    const labels = nouveauTransformateur.querySelectorAll('label');
    labels.forEach(label => {
        if (label.getAttribute('for')) {
            label.setAttribute('for', 
                label.getAttribute('for').replace('_0_', `_${compteurTransformateurs}_`)
            );
        }
    });
    
    // Mettre à jour le titre
    const titre = nouveauTransformateur.querySelector('.card-header h6');
    if (titre) {
        titre.innerHTML = `<i class="fas fa-cog me-2"></i>Transformateur ${compteurTransformateurs + 1} - Nouveau`;
    }
    
    // Mettre à jour le bouton de suppression
    const btnSupprimer = nouveauTransformateur.querySelector('.btn-outline-danger');
    if (btnSupprimer) {
        btnSupprimer.setAttribute('onclick', `supprimerTransformateur(${compteurTransformateurs})`);
    }
    
    // Ajouter au container
    container.appendChild(nouveauTransformateur);
    
    // Animation d'apparition
    nouveauTransformateur.style.opacity = '0';
    nouveauTransformateur.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        nouveauTransformateur.style.transition = 'all 0.3s ease';
        nouveauTransformateur.style.opacity = '1';
        nouveauTransformateur.style.transform = 'translateY(0)';
    }, 100);
    
    // Scroll vers le nouveau transformateur
    nouveauTransformateur.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
    
    // Mettre à jour le compteur
    mettreAJourCompteurTransformateurs();
}

/**
 * Supprimer un transformateur
 */
function supprimerTransformateur(index) {
    const transformateur = document.getElementById(`transformateur-${index}`);
    
    if (!transformateur) {
        console.error(`Transformateur ${index} non trouvé`);
        return;
    }
    
    // Confirmation
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce transformateur ?')) {
        return;
    }
    
    // Animation de disparition
    transformateur.style.transition = 'all 0.3s ease';
    transformateur.style.opacity = '0';
    transformateur.style.transform = 'translateX(-100%)';
    
    setTimeout(() => {
        transformateur.remove();
        mettreAJourCompteurTransformateurs();
        renumeroterTransformateurs();
    }, 300);
}

/**
 * Mettre à jour le compteur de transformateurs
 */
function mettreAJourCompteurTransformateurs() {
    const container = document.getElementById('transformateurs-container');
    const transformateurs = container ? container.querySelectorAll('[id^="transformateur-"]:not(#transformateur-template)') : [];
    const compteur = document.getElementById('compteur-transformateurs');
    
    if (compteur) {
        compteur.textContent = transformateurs.length;
    }
    
    // Afficher/masquer le message vide
    const messageVide = document.getElementById('aucun-transformateur');
    if (messageVide) {
        messageVide.style.display = transformateurs.length === 0 ? 'block' : 'none';
    }
    
    // Activer/désactiver le bouton de suppression
    const boutonsSupprimer = document.querySelectorAll('.btn-supprimer-transformateur');
    boutonsSupprimer.forEach(btn => {
        btn.disabled = transformateurs.length <= 1;
    });
}

/**
 * Renuméroter les transformateurs après suppression
 */
function renumeroterTransformateurs() {
    const container = document.getElementById('transformateurs-container');
    if (!container) return;
    
    const transformateurs = container.querySelectorAll('[id^="transformateur-"]:not(#transformateur-template)');
    
    transformateurs.forEach((transformateur, index) => {
        // Mettre à jour l'ID
        transformateur.id = `transformateur-${index}`;
        
        // Mettre à jour le titre
        const titre = transformateur.querySelector('.card-header h6');
        if (titre) {
            const nomTransformateur = transformateur.querySelector('input[name*="nom"]')?.value || 'Nouveau';
            titre.innerHTML = `<i class="fas fa-cog me-2"></i>Transformateur ${index + 1} - ${nomTransformateur}`;
        }
        
        // Mettre à jour le bouton de suppression
        const btnSupprimer = transformateur.querySelector('.btn-outline-danger');
        if (btnSupprimer) {
            btnSupprimer.setAttribute('onclick', `supprimerTransformateur(${index})`);
        }
        
        // Mettre à jour les noms des champs
        const champs = transformateur.querySelectorAll('input, select, textarea');
        champs.forEach(champ => {
            if (champ.name) {
                // Remplacer l'ancien index par le nouveau
                champ.name = champ.name.replace(/\[\d+\]/, `[${index}]`);
                champ.id = champ.id.replace(/_\d+_/, `_${index}_`);
            }
        });
        
        // Mettre à jour les labels
        const labels = transformateur.querySelectorAll('label');
        labels.forEach(label => {
            if (label.getAttribute('for')) {
                label.setAttribute('for', 
                    label.getAttribute('for').replace(/_\d+_/, `_${index}_`)
                );
            }
        });
    });
}

/**
 * Mettre à jour le titre d'un transformateur quand son nom change
 */
function mettreAJourTitreTransformateur(input, index) {
    const titre = document.querySelector(`#transformateur-${index} .card-header h6`);
    if (titre) {
        const nom = input.value || 'Nouveau';
        titre.innerHTML = `<i class="fas fa-cog me-2"></i>Transformateur ${index + 1} - ${nom}`;
    }
}

/**
 * Calculer automatiquement les pertes et rendement
 */
function calculerPerformances(index) {
    const transformateur = document.getElementById(`transformateur-${index}`);
    if (!transformateur) return;
    
    const puissance = parseFloat(transformateur.querySelector('[name*="puissance_nominale"]')?.value) || 0;
    const pertesVide = parseFloat(transformateur.querySelector('[name*="pertes_vide"]')?.value) || 0;
    const pertesCharge = parseFloat(transformateur.querySelector('[name*="pertes_charge"]')?.value) || 0;
    
    if (puissance > 0) {
        // Calcul du rendement à pleine charge
        const pertesTotales = pertesVide + pertesCharge;
        const puissanceUtile = puissance * 1000; // Conversion en kW
        const rendement = ((puissanceUtile - pertesTotales) / puissanceUtile * 100).toFixed(2);
        
        // Affichage du rendement (si le champ existe)
        const champRendement = transformateur.querySelector('[name*="rendement"]');
        if (champRendement) {
            champRendement.value = rendement;
        }
        
        // Calcul des pertes relatives
        const pertesRelatives = (pertesTotales / puissanceUtile * 100).toFixed(3);
        
        // Affichage dans un badge informatif
        let badgeInfo = transformateur.querySelector('.badge-performances');
        if (!badgeInfo) {
            badgeInfo = document.createElement('span');
            badgeInfo.className = 'badge bg-info badge-performances ms-2';
            const titre = transformateur.querySelector('.card-header h6');
            if (titre) {
                titre.appendChild(badgeInfo);
            }
        }
        
        badgeInfo.textContent = `η = ${rendement}%`;
        badgeInfo.title = `Rendement: ${rendement}% | Pertes: ${pertesRelatives}%`;
    }
}

/**
 * Valider les données d'un transformateur
 */
function validerTransformateur(index) {
    const transformateur = document.getElementById(`transformateur-${index}`);
    if (!transformateur) return false;
    
    const erreurs = [];
    
    // Vérifications obligatoires
    const nom = transformateur.querySelector('[name*="nom"]')?.value;
    if (!nom || nom.trim() === '') {
        erreurs.push('Le nom du transformateur est obligatoire');
    }
    
    const puissance = parseFloat(transformateur.querySelector('[name*="puissance_nominale"]')?.value);
    if (!puissance || puissance <= 0) {
        erreurs.push('La puissance nominale doit être supérieure à 0');
    }
    
    const tensionPrimaire = parseFloat(transformateur.querySelector('[name*="tension_primaire"]')?.value);
    const tensionSecondaire = parseFloat(transformateur.querySelector('[name*="tension_secondaire"]')?.value);
    
    if (!tensionPrimaire || tensionPrimaire <= 0) {
        erreurs.push('La tension primaire doit être supérieure à 0');
    }
    
    if (!tensionSecondaire || tensionSecondaire <= 0) {
        erreurs.push('La tension secondaire doit être supérieure à 0');
    }
    
    // Vérifications logiques
    if (tensionPrimaire && tensionSecondaire && tensionPrimaire <= tensionSecondaire) {
        erreurs.push('La tension primaire doit être supérieure à la tension secondaire');
    }
    
    const impedance = parseFloat(transformateur.querySelector('[name*="impedance_cc"]')?.value);
    if (impedance && (impedance < 0 || impedance > 100)) {
        erreurs.push('L\'impédance de court-circuit doit être entre 0 et 100%');
    }
    
    // Affichage des erreurs
    if (erreurs.length > 0) {
        const alertContainer = transformateur.querySelector('.alert-container') || 
                              creerContainerAlerte(transformateur);
        
        alertContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <strong>Erreurs de validation :</strong>
                <ul class="mb-0 mt-2">
                    ${erreurs.map(erreur => `<li>${erreur}</li>`).join('')}
                </ul>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Scroll vers l'erreur
        alertContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        return false;
    }
    
    // Supprimer les anciennes alertes si validation réussie
    const ancienneAlerte = transformateur.querySelector('.alert-container');
    if (ancienneAlerte) {
        ancienneAlerte.innerHTML = '';
    }
    
    return true;
}

/**
 * Créer un container pour les alertes
 */
function creerContainerAlerte(transformateur) {
    let container = transformateur.querySelector('.alert-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'alert-container mt-3';
        transformateur.querySelector('.card-body').insertBefore(
            container, 
            transformateur.querySelector('.card-body').firstChild
        );
    }
    return container;
}

/**
 * Exporter les données des transformateurs
 */
function exporterTransformateurs() {
    const transformateurs = [];
    const containers = document.querySelectorAll('[id^="transformateur-"]:not(#transformateur-template)');
    
    containers.forEach((container, index) => {
        const data = {};
        const champs = container.querySelectorAll('input, select, textarea');
        
        champs.forEach(champ => {
            if (champ.name && champ.value) {
                const nom = champ.name.replace(/.*\[.*\]\./, '');
                data[nom] = champ.value;
            }
        });
        
        if (Object.keys(data).length > 0) {
            transformateurs.push(data);
        }
    });
    
    return transformateurs;
}

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Compter les transformateurs existants
    mettreAJourCompteurTransformateurs();
    
    // Ajouter les event listeners pour la validation en temps réel
    document.addEventListener('change', function(e) {
        if (e.target.matches('[name*="puissance_nominale"], [name*="pertes_vide"], [name*="pertes_charge"]')) {
            const container = e.target.closest('[id^="transformateur-"]');
            if (container) {
                const index = container.id.replace('transformateur-', '');
                calculerPerformances(index);
            }
        }
        
        if (e.target.matches('[name*="nom"]')) {
            const container = e.target.closest('[id^="transformateur-"]');
            if (container) {
                const index = container.id.replace('transformateur-', '');
                mettreAJourTitreTransformateur(e.target, index);
            }
        }
    });
    
    // Event listener pour la validation avant soumission
    const formulaire = document.querySelector('form');
    if (formulaire) {
        formulaire.addEventListener('submit', function(e) {
            let tousValides = true;
            const transformateurs = document.querySelectorAll('[id^="transformateur-"]:not(#transformateur-template)');
            
            transformateurs.forEach((transformateur, index) => {
                if (!validerTransformateur(index)) {
                    tousValides = false;
                }
            });
            
            if (!tousValides) {
                e.preventDefault();
                alert('Veuillez corriger les erreurs avant de continuer.');
            }
        });
    }
});

// Fonctions utilitaires pour les graphiques
function creerGraphiqueChargeTransformateur(containerId, data) {
    const ctx = document.getElementById(containerId);
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Charge (%)',
                data: data.charges,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Charge (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution de la charge'
                }
            }
        }
    });
}