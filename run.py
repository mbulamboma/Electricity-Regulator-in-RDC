"""
Point d'entrée de l'application Flask
"""
import os
from app import create_app
from app.extensions import db
from app.utils import init_database, create_admin_user, seed_sample_data

app = create_app()


@app.cli.command()
def init_db():
    """Initialiser la base de données"""
    with app.app_context():
        init_database()
        print("Base de données initialisée!")


@app.cli.command()
def create_admin():
    """Créer un utilisateur administrateur"""
    with app.app_context():
        username = input("Nom d'utilisateur (admin): ") or "admin"
        email = input("Email (admin@example.com): ") or "admin@example.com"
        password = input("Mot de passe (admin123): ") or "admin123"
        
        create_admin_user(username, email, password)


@app.cli.command()
def init_are_data():
    """Initialiser les données d'exemple ARE"""
    with app.app_context():
        from ajouter_donnees_are import ajouter_donnees_simples
        
        print("🚀 Initialisation des données ARE...")
        if ajouter_donnees_simples():
            print("✅ Données ARE initialisées avec succès!")
        else:
            print("❌ Échec de l'initialisation des données ARE")


@app.cli.command()
def seed_data():
    """Ajouter des données d'exemple"""
    with app.app_context():
        seed_sample_data()


@app.cli.command()
def reset_db():
    """Réinitialiser complètement la base de données"""
    with app.app_context():
        if input("Êtes-vous sûr de vouloir réinitialiser la base de données ? (yes/no): ") == "yes":
            from app.utils import reset_database
            reset_database()
            create_admin_user()
            seed_sample_data()
            print("Base de données réinitialisée avec succès!")
        else:
            print("Opération annulée.")


@app.shell_context_processor
def make_shell_context():
    """Contexte du shell Flask"""
    from app.models import User, Operateur
    return {
        'db': db,
        'User': User,
        'Operateur': Operateur
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
