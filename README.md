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

- **Django 4.2.23** : Framework web Python
- **MongoDB Atlas** : Base de données NoSQL
- **MongoEngine** : ODM pour MongoDB
- **GraphQL** : API moderne avec graphene-django
- **JWT** : Authentification sécurisée
- **CORS** : Support cross-origin pour React

## 📋 Prérequis

- Python 3.8+
- MongoDB Atlas (ou MongoDB local)
- pip

### Prérequis optionnels pour la génération IA

- **Pour les images** : Token Hugging Face (requis pour générer des images)
- **Pour la musique** :
  - GPU recommandé (NVidia avec CUDA) pour des temps de génération rapides
  - Au moins 8GB RAM
  - ~3GB d'espace disque libre pour le modèle MusicGen

## 🔧 Installation

1. **Cloner le projet**

```bash
git clone <repository-url>
cd veh-backend-django
```

2. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement**

```bash
cp env.example .env
```

4. **Lancer le serveur de développement**

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

- **GraphiQL Interface** : `http://localhost:8000/graphql/` (interface interactive pour tester l'API)
- **Collection Postman** : Importer `VEH.postman_collection.json` dans Postman pour tester les endpoints GraphQL

### Authentification

Pour les requêtes authentifiées, inclure le token JWT dans le header :

```
Authorization: JWT <votre_token_jwt>
```

Le token est obtenu via la mutation `login` ou `tokenAuth` (fournie par `graphql-jwt`).

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
- **Génération d'assets via IA** ✨
  - Images générées via Hugging Face Stable Diffusion
  - Sons générés via gTTS (Text-to-Speech) pour la narration (stocké dans `sound_id`)
  - Musique d'ambiance générée via MusicGen (stockée dans `music_id`, séparée du TTS)
  - Génération automatique lors de la création de scènes (via les flags `auto_generate_image`, `auto_generate_sound`, `auto_generate_music`)
  - Mutation `generate_asset` disponible pour générer manuellement des assets

#### 📌 Modes de génération IA disponibles

Le système supporte 3 types de génération :

1. **Images** (nécessite `HUGGINGFACE_API_TOKEN`) : Générées via Hugging Face API
2. **Voix/TTS** (aucune config requise) : Génération vocale gratuite via gTTS
3. **Musique d'ambiance** (optionnel) : Génération locale via MusicGen

> **Note importante** : La génération musicale fonctionne localement et nécessite des ressources importantes. Si vous n'avez pas de GPU ou si vous ne souhaitez pas utiliser cette fonctionnalité, le système continuera de fonctionner normalement. La génération de musique retournera une erreur explicite si les dépendances requises ne sont pas installées.

## 🔒 Sécurité

- **Authentification JWT** : Tokens sécurisés signés avec `SECRET_KEY`
- **Header d'authentification** : Utiliser le préfixe `JWT ` dans le header `Authorization` (ex: `Authorization: JWT <token>`)
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
MONGODB_DB_NAME=your-database-name
JWT_EXPIRATION_DELTA=3600
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

> **Note** : `SECRET_KEY` est utilisé à la fois pour Django et pour signer les tokens JWT. Les variables `JWT_SECRET_KEY` et `JWT_ALGORITHM` présentes dans `env.example` ne sont pas utilisées par le code actuel.

### Commandes de déploiement

```bash
# Collecter les fichiers statiques (si nécessaire)
python manage.py collectstatic

# Note: MongoDB/MongoEngine n'utilise pas de migrations Django
# Les collections sont créées automatiquement lors de la première utilisation

# Lancer le serveur avec Gunicorn
gunicorn interactive_story_backend.wsgi:application
```

### Installation

Toutes les dépendances pour la génération IA sont déjà dans `requirements.txt`. L'installation standard suffit :

```bash
pip install -r requirements.txt
```

### Configuration

**Pour les images** (requis si vous voulez générer des images) :

1. Créez un compte sur [Hugging Face](https://huggingface.co/)
2. Générez un token d'accès dans vos paramètres
3. Ajoutez `HUGGINGFACE_API_TOKEN=votre_token` dans votre `.env`
4. Optionnel : Configurez le modèle d'image avec `HF_IMAGE_MODEL` (défaut: `stabilityai/stable-diffusion-xl-base-1.0`)

**Pour la musique** (optionnel) :

- Le système détecte automatiquement si les bibliothèques ML (`transformers`, `torch`) sont installées
- Si non, la génération musicale est désactivée avec un message d'erreur clair
- Optionnel : Configurez le modèle MusicGen avec `MUSICGEN_MODEL` dans votre `.env` (défaut: `facebook/musicgen-small`)
- **Note** : La durée de génération est limitée à 15 secondes maximum pour optimiser les performances

### Premier démarrage - Téléchargement des modèles

Lors de la **première** génération de musique :

- Le modèle MusicGen sera automatiquement téléchargé depuis Hugging Face
- Taille : ~3GB pour `musicgen-small`
- Temps : 10-15 minutes selon la connexion
- Cache : Le modèle est mis en cache pour les utilisations suivantes

### Performance

**Génération musicale** :

- **Durée par défaut** : 15 secondes (limité à 15s maximum pour des raisons de performance)
- **Avec GPU** : ~1-2 minutes pour 15s de musique
- **Avec CPU** : ~5-10 minutes pour 15s de musique
- **Recommandation** : Utiliser GPU ou éviter cette fonctionnalité en production

**Autres générations** :

- Images : ~10-30 secondes (dépend de l'API Hugging Face)
- TTS : ~1-5 secondes (très rapide)

### Conseils pour les développeurs

Si vous ne souhaitez **pas** utiliser la génération musicale :

- Le système fonctionne parfaitement sans GPU
- Les fonctionnalités images et TTS restent disponibles
- Les erreurs de génération musicale n'affectent pas le reste de l'API
- Vous pouvez uploader vos propres fichiers via `create_asset`

## 📊 Monitoring et Debug

- **GraphiQL Interface** : Interface interactive disponible à `http://localhost:8000/graphql/`
- **Logs Django** : Logs détaillés des requêtes via la console
- **Collection Postman** : Utiliser `VEH.postman_collection.json` pour tester toutes les mutations et queries

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.
