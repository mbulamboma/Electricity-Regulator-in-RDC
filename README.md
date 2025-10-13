# Régulation Électricité RDC

Application Flask modulaire pour la gestion et la régulation des opérateurs d'électricité en République Démocratique du Congo.

## 🚀 Fonctionnalités

- ✅ Système d'authentification complet (inscription, connexion, déconnexion)
- ✅ Gestion des utilisateurs avec différents rôles (admin, user, operateur)
- ✅ Gestion des opérateurs d'électricité
- ✅ Tableau de bord administratif
- ✅ Base de données SQLite
- ✅ Interface responsive avec Bootstrap 5

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## 🔧 Installation

1. **Cloner le projet** (si applicable)
```bash
cd regulation_electricite
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

Windows (CMD):
```cmd
venv\Scripts\activate.bat
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## 🗄️ Configuration de la base de données

1. **Initialiser la base de données**
```bash
flask --app run init-db
```

2. **Créer un utilisateur administrateur**
```bash
flask --app run create-admin
```

3. **Ajouter des données d'exemple** (optionnel)
```bash
flask --app run seed-data
```

## ▶️ Lancement de l'application

1. **Démarrer le serveur de développement**
```bash
python run.py
```

Ou avec Flask CLI:
```bash
flask --app run run --debug
```

2. **Accéder à l'application**
Ouvrez votre navigateur et allez à: http://localhost:5000

## 👤 Connexion par défaut

- **Nom d'utilisateur**: admin
- **Mot de passe**: admin123

⚠️ **Important**: Changez ces identifiants en production!

## 📁 Structure du projet

```
regulation_electricite/
├── app/
│   ├── __init__.py              # Factory de l'application
│   ├── config.py                # Configurations
│   ├── extensions.py            # Extensions Flask
│   ├── models/                  # Modèles de base de données
│   │   ├── __init__.py
│   │   ├── base.py             # Modèle de base
│   │   ├── utilisateurs.py     # Modèle User
│   │   └── operateurs.py       # Modèle Operateur
│   ├── auth/                    # Module d'authentification
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── templates/               # Templates HTML
│   │   ├── base.html
│   │   ├── auth/
│   │   └── admin/
│   ├── static/                  # Fichiers statiques
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/                   # Utilitaires
│       ├── __init__.py
│       ├── database.py
│       └── helpers.py
├── instance/                    # Fichiers d'instance (DB)
├── migrations/                  # Migrations de base de données
├── requirements.txt             # Dépendances Python
├── run.py                       # Point d'entrée
└── README.md                    # Documentation
```

## 🛠️ Commandes utiles

### Gestion de la base de données

```bash
# Initialiser la base de données
flask --app run init-db

# Créer un administrateur
flask --app run create-admin

# Ajouter des données d'exemple
flask --app run seed-data

# Réinitialiser la base de données
flask --app run reset-db
```

### Shell interactif

```bash
flask --app run shell
```

Dans le shell, vous avez accès à:
- `db`: L'instance SQLAlchemy
- `User`: Le modèle User
- `Operateur`: Le modèle Operateur

## 🔒 Sécurité

- Les mots de passe sont hashés avec Bcrypt
- Protection CSRF sur tous les formulaires
- Sessions sécurisées
- Validation des données d'entrée

## 🌍 Variables d'environnement

Créez un fichier `.env` à la racine du projet:

```env
FLASK_ENV=development
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
DATABASE_URL=sqlite:///instance/database.db
```

## 📝 Développement

### Ajouter un nouveau module

1. Créer un nouveau Blueprint dans `app/`
2. Enregistrer le Blueprint dans `app/__init__.py`
3. Ajouter les routes et templates nécessaires

### Ajouter un nouveau modèle

1. Créer le modèle dans `app/models/`
2. Importer le modèle dans `app/models/__init__.py`
3. Créer une migration si nécessaire

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à:
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 📧 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue.

---

Développé avec ❤️ pour la régulation du secteur électrique en RDC
