# Backend Django - Application Narratif Interactif

Backend Django pour une application de livre dont vous êtes le héros, connecté à MongoDB Atlas et exposant une API GraphQL.

## 🚀 Fonctionnalités

- **Gestion des utilisateurs** : Admins (créateurs de scénarios) et joueurs
- **Scénarios narratifs** : Création et gestion de scénarios interactifs
- **Scènes et choix** : Système de scènes reliées par des choix
- **Suivi de progression** : Suivi du parcours des joueurs dans les scénarios
- **Gestion d'assets** : Images et sons pour enrichir les scènes
- **API GraphQL** : Interface moderne et flexible
- **Authentification JWT** : Sécurisation des endpoints
- **Base de données MongoDB** : Stockage flexible et scalable

## 🛠️ Stack Technique

- **Django 4.2** : Framework web Python
- **MongoDB Atlas** : Base de données NoSQL
- **MongoEngine** : ODM pour MongoDB
- **GraphQL** : API moderne avec graphene-django
- **JWT** : Authentification sécurisée
- **CORS** : Support cross-origin pour React

## 📋 Prérequis

- Python 3.8+
- MongoDB Atlas (ou MongoDB local)
- pip

## 🔧 Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd backend-django
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement**
```bash
cp env.example .env
```

Éditer le fichier `.env` avec ces configurations :
```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Atlas Settings
MONGODB_URI=mongodb+srv://morganrajaonarivony5:morgan1234@cluster0.c480fh7.mongodb.net/veh_tpi?retryWrites=true&w=majority&appName=Cluster0
MONGODB_DB_NAME=veh_tpi

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 
```

5. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

## 🗄️ Structure de la Base de Données

### Collections MongoDB

1. **users** : Gestion des utilisateurs (admins/joueurs)
2. **scenarios** : Scénarios narratifs
3. **scenes** : Scènes dans les scénarios
4. **choices** : Choix entre scènes
5. **player_progress** : Progression des joueurs
6. **assets** : Images et sons

## 🔌 API GraphQL

### Endpoint
- **GraphQL Playground** : `http://localhost:8000/graphql/`
- **A importer dans postman pour tester les endpoints GraphQL** : voir `VEH.postman_collection.json`


## 📱 Applications Django

### 1. **users** - Gestion des utilisateurs
- Modèle User avec rôles admin/player
- Authentification JWT
- Hachage sécurisé des mots de passe

### 2. **stories** - Scénarios narratifs
- Modèles Scenario, Scene, Choice
- Relations entre scènes et choix
- Gestion des auteurs

### 3. **progress** - Suivi de progression
- Modèle PlayerProgress
- Historique des choix
- Calcul de progression

### 4. **assets** - Gestion des médias
- Modèle Asset pour images/sons
- Métadonnées des fichiers
- Génération d'assets (placeholder IA)

## 🔒 Sécurité

- **Authentification JWT** : Tokens sécurisés
- **Autorisations** : Contrôle d'accès par rôle
- **Validation** : Validation des données GraphQL
- **CORS** : Configuration sécurisée pour React

## 🚀 Déploiement

### Variables d'environnement de production
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com
MONGODB_URI=your-production-mongodb-uri
```

### Commandes de déploiement
```bash
python manage.py collectstatic
python manage.py migrate
gunicorn interactive_story_backend.wsgi:application
```

## 📊 Monitoring et Debug

- **GraphQL Playground** : Interface interactive pour tester l'API
- **Debug GraphQL** : Query `__debug` disponible en développement
- **Logs Django** : Logs détaillés des requêtes

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.