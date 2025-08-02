#!/usr/bin/env python3
"""
Script de peuplement initial pour l'application de livre dont vous êtes le héros.
Ce script crée des données d'exemple pour tester l'API.
"""

import os
import sys
import django
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interactive_story_backend.settings')
django.setup()

from users.models import User
from stories.models import Scenario, Scene, Choice
from assets.models import Asset
from progress.models import PlayerProgress


def create_sample_users():
    """Créer des utilisateurs d'exemple"""
    print("Création des utilisateurs d'exemple...")
    
    # Admin
    admin_user = User(
        email="admin@example.com",
        password="admin123",
        role="admin",
        first_name="Admin",
        last_name="User"
    )
    admin_user.save()
    print(f"✓ Admin créé: {admin_user.email}")
    
    # Joueur 1
    player1 = User(
        email="player1@example.com",
        password="player123",
        role="player",
        first_name="Alice",
        last_name="Joueur"
    )
    player1.save()
    print(f"✓ Joueur créé: {player1.email}")
    
    # Joueur 2
    player2 = User(
        email="player2@example.com",
        password="player123",
        role="player",
        first_name="Bob",
        last_name="Joueur"
    )
    player2.save()
    print(f"✓ Joueur créé: {player2.email}")
    
    return admin_user, player1, player2


def create_sample_assets(admin_user):
    """Créer des assets d'exemple"""
    print("Création des assets d'exemple...")
    
    # Image de forêt
    forest_image = Asset(
        type="image",
        name="Forêt sombre",
        filename="forest_dark.jpg",
        url="https://example.com/images/forest_dark.jpg",
        file_size=1024 * 512,  # 512KB
        mime_type="image/jpeg",
        metadata={
            "width": 1920,
            "height": 1080,
            "description": "Une forêt sombre et mystérieuse"
        },
        uploaded_by=admin_user,
        is_public=True
    )
    forest_image.save()
    print(f"✓ Asset créé: {forest_image.name}")
    
    # Son d'ambiance
    ambient_sound = Asset(
        type="sound",
        name="Ambiance forestière",
        filename="forest_ambient.mp3",
        url="https://example.com/sounds/forest_ambient.mp3",
        file_size=1024 * 2048,  # 2MB
        mime_type="audio/mpeg",
        metadata={
            "duration": 180,  # 3 minutes
            "description": "Sons de la forêt"
        },
        uploaded_by=admin_user,
        is_public=True
    )
    ambient_sound.save()
    print(f"✓ Asset créé: {ambient_sound.name}")
    
    return forest_image, ambient_sound


def create_sample_scenario(admin_user, forest_image, ambient_sound):
    """Créer un scénario d'exemple complet"""
    print("Création du scénario d'exemple...")
    
    # Créer le scénario
    scenario = Scenario(
        title="La Forêt Maudite",
        description="Une aventure mystérieuse dans une forêt sombre où chaque choix compte.",
        author_id=admin_user,
        is_published=True
    )
    scenario.save()
    print(f"✓ Scénario créé: {scenario.title}")
    
    # Créer les scènes
    scenes = []
    
    # Scène 1 - Début
    scene1 = Scene(
        scenario_id=scenario,
        title="Entrée de la forêt",
        text="Vous vous trouvez à l'entrée d'une forêt sombre et mystérieuse. Les arbres semblent s'étendre à l'infini. Un chemin se divise devant vous.",
        order=1,
        image_id=forest_image,
        sound_id=ambient_sound,
        is_start_scene=True
    )
    scene1.save()
    scenes.append(scene1)
    print(f"✓ Scène créée: {scene1.title}")
    
    # Scène 2 - Chemin de gauche
    scene2 = Scene(
        scenario_id=scenario,
        title="Le chemin de gauche",
        text="Vous prenez le chemin de gauche. Il mène vers une clairière éclairée par la lune. Vous entendez des bruits étranges.",
        order=2,
        image_id=forest_image
    )
    scene2.save()
    scenes.append(scene2)
    print(f"✓ Scène créée: {scene2.title}")
    
    # Scène 3 - Chemin de droite
    scene3 = Scene(
        scenario_id=scenario,
        title="Le chemin de droite",
        text="Vous prenez le chemin de droite. Il descend vers une rivière sombre. L'eau coule lentement.",
        order=3,
        image_id=forest_image
    )
    scene3.save()
    scenes.append(scene3)
    print(f"✓ Scène créée: {scene3.title}")
    
    # Scène 4 - Clairière mystérieuse
    scene4 = Scene(
        scenario_id=scenario,
        title="Clairière mystérieuse",
        text="Dans la clairière, vous découvrez une ancienne pierre gravée de symboles mystérieux. Que faites-vous ?",
        order=4,
        image_id=forest_image
    )
    scene4.save()
    scenes.append(scene4)
    print(f"✓ Scène créée: {scene4.title}")
    
    # Scène 5 - Rivière sombre
    scene5 = Scene(
        scenario_id=scenario,
        title="Rivière sombre",
        text="Au bord de la rivière, vous voyez un pont branlant. Il semble fragile mais c'est le seul moyen de traverser.",
        order=5,
        image_id=forest_image
    )
    scene5.save()
    scenes.append(scene5)
    print(f"✓ Scène créée: {scene5.title}")
    
    # Scène 6 - Fin (succès)
    scene6 = Scene(
        scenario_id=scenario,
        title="Découverte du trésor",
        text="Félicitations ! Vous avez découvert le trésor caché de la forêt. Votre aventure se termine ici.",
        order=6,
        image_id=forest_image,
        is_end_scene=True
    )
    scene6.save()
    scenes.append(scene6)
    print(f"✓ Scène créée: {scene6.title}")
    
    # Scène 7 - Fin (échec)
    scene7 = Scene(
        scenario_id=scenario,
        title="Piège mortel",
        text="Oh non ! Vous êtes tombé dans un piège. Votre aventure se termine tragiquement.",
        order=7,
        image_id=forest_image,
        is_end_scene=True
    )
    scene7.save()
    scenes.append(scene7)
    print(f"✓ Scène créée: {scene7.title}")
    
    # Créer les choix
    choices = []
    
    # Choix depuis la scène 1
    choice1 = Choice(
        from_scene_id=scene1,
        to_scene_id=scene2,
        text="Prendre le chemin de gauche",
        order=1
    )
    choice1.save()
    choices.append(choice1)
    
    choice2 = Choice(
        from_scene_id=scene1,
        to_scene_id=scene3,
        text="Prendre le chemin de droite",
        order=2
    )
    choice2.save()
    choices.append(choice2)
    
    # Choix depuis la scène 2
    choice3 = Choice(
        from_scene_id=scene2,
        to_scene_id=scene4,
        text="Explorer la clairière",
        order=1
    )
    choice3.save()
    choices.append(choice3)
    
    # Choix depuis la scène 3
    choice4 = Choice(
        from_scene_id=scene3,
        to_scene_id=scene5,
        text="Suivre la rivière",
        order=1
    )
    choice4.save()
    choices.append(choice4)
    
    # Choix depuis la scène 4
    choice5 = Choice(
        from_scene_id=scene4,
        to_scene_id=scene6,
        text="Étudier les symboles",
        order=1
    )
    choice5.save()
    choices.append(choice5)
    
    choice6 = Choice(
        from_scene_id=scene4,
        to_scene_id=scene7,
        text="Toucher la pierre",
        order=2
    )
    choice6.save()
    choices.append(choice6)
    
    # Choix depuis la scène 5
    choice7 = Choice(
        from_scene_id=scene5,
        to_scene_id=scene6,
        text="Traverser le pont",
        order=1
    )
    choice7.save()
    choices.append(choice7)
    
    choice8 = Choice(
        from_scene_id=scene5,
        to_scene_id=scene7,
        text="Chercher un autre passage",
        order=2
    )
    choice8.save()
    choices.append(choice8)
    
    print(f"✓ {len(choices)} choix créés")
    
    # Ajouter les scènes et choix au scénario
    scenario.scenes = scenes
    scenario.save()
    
    # Ajouter les choix aux scènes
    scene1.choices = [choice1, choice2]
    scene1.save()
    
    scene2.choices = [choice3]
    scene2.save()
    
    scene3.choices = [choice4]
    scene3.save()
    
    scene4.choices = [choice5, choice6]
    scene4.save()
    
    scene5.choices = [choice7, choice8]
    scene5.save()
    
    return scenario


def create_sample_progress(player1, player2, scenario):
    """Créer des progressions d'exemple"""
    print("Création des progressions d'exemple...")
    
    # Progression pour player1
    progress1 = PlayerProgress(
        user_id=player1,
        scenario_id=scenario,
        current_scene_id=scenario.scenes[1],  # Scène 2
        total_time_spent=300  # 5 minutes
    )
    progress1.save()
    print(f"✓ Progression créée pour {player1.email}")
    
    # Progression pour player2
    progress2 = PlayerProgress(
        user_id=player2,
        scenario_id=scenario,
        current_scene_id=scenario.scenes[2],  # Scène 3
        total_time_spent=180  # 3 minutes
    )
    progress2.save()
    print(f"✓ Progression créée pour {player2.email}")
    
    return progress1, progress2


def main():
    """Fonction principale du script de peuplement"""
    print("🌱 Début du peuplement des données d'exemple...")
    print("=" * 50)
    
    try:
        # Créer les utilisateurs
        admin_user, player1, player2 = create_sample_users()
        
        # Créer les assets
        forest_image, ambient_sound = create_sample_assets(admin_user)
        
        # Créer le scénario complet
        scenario = create_sample_scenario(admin_user, forest_image, ambient_sound)
        
        # Créer les progressions
        progress1, progress2 = create_sample_progress(player1, player2, scenario)
        
        print("=" * 50)
        print("✅ Peuplement terminé avec succès !")
        print("\n📊 Résumé :")
        print(f"   - {User.objects.count()} utilisateurs créés")
        print(f"   - {Asset.objects.count()} assets créés")
        print(f"   - {Scenario.objects.count()} scénario créé")
        print(f"   - {Scene.objects.count()} scènes créées")
        print(f"   - {Choice.objects.count()} choix créés")
        print(f"   - {PlayerProgress.objects.count()} progressions créées")
        
        print("\n🔑 Identifiants de connexion :")
        print("   Admin: admin@example.com / admin123")
        print("   Joueur 1: player1@example.com / player123")
        print("   Joueur 2: player2@example.com / player123")
        
        print("\n🌐 Accès à l'API :")
        print("   GraphQL Playground: http://localhost:8000/graphql/")
        print("   JWT Endpoints: http://localhost:8000/graphql-jwt/")
        
    except Exception as e:
        print(f"❌ Erreur lors du peuplement : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 