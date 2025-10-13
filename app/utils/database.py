"""
Utilitaires pour la base de données
"""
from app.extensions import db
from app.models import User, Operateur


def init_database():
    """Initialiser la base de données avec les tables"""
    db.create_all()
    print("Tables créées avec succès!")


def create_admin_user(username='admin', email='admin@example.com', password='admin123'):
    """Créer un utilisateur administrateur par défaut"""
    admin = User.query.filter_by(username=username).first()
    
    if not admin:
        admin = User(
            username=username,
            email=email,
            nom='Administrateur',
            prenom='Système',
            role='admin'
        )
        admin.set_password(password)
        admin.save()
        print(f"Administrateur créé: {username}")
        return admin
    else:
        print(f"L'administrateur {username} existe déjà")
        return admin


def seed_sample_data():
    """Ajouter des données d'exemple"""
    # Vérifier si des opérateurs existent déjà
    if Operateur.query.count() > 0:
        print("Des opérateurs existent déjà dans la base de données")
        return
    
    # Créer des opérateurs d'exemple
    operateurs_exemple = [
        {
            'nom': 'Société Nationale d\'Électricité',
            'sigle': 'SNEL',
            'type_operateur': 'Production',
            'ville': 'Kinshasa',
            'province': 'Kinshasa',
            'telephone': '+243 123 456 789',
            'email': 'contact@snel.cd',
            'numero_licence': 'LIC-001-2024',
            'statut_licence': 'active',
            'capacite_installee': 2500.0,
            'nombre_clients': 500000
        },
        {
            'nom': 'Énergie du Congo',
            'sigle': 'EDC',
            'type_operateur': 'Distribution',
            'ville': 'Lubumbashi',
            'province': 'Haut-Katanga',
            'telephone': '+243 987 654 321',
            'email': 'info@edc.cd',
            'numero_licence': 'LIC-002-2024',
            'statut_licence': 'active',
            'capacite_installee': 150.0,
            'nombre_clients': 75000
        }
    ]
    
    for op_data in operateurs_exemple:
        operateur = Operateur(**op_data)
        operateur.save()
    
    print(f"{len(operateurs_exemple)} opérateurs d'exemple créés!")


def reset_database():
    """Réinitialiser complètement la base de données"""
    db.drop_all()
    print("Tables supprimées")
    init_database()
    print("Base de données réinitialisée")
