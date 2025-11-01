#!/usr/bin/env python3
"""
Script de peuplement initial pour l'application de livre dont vous êtes le héros.
Ce script crée le scénario "Le Château Oublié" avec toutes ses scènes, assets générés via IA, et choices.

Usage:
    python fixtures/seed_data.py
    ou
    python manage.py shell < fixtures/seed_data.py
"""

import os
import sys
import django
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interactive_story_backend.settings")
django.setup()

# S'assurer que MongoDB est bien connecté
import mongoengine
from django.conf import settings
from decouple import config

MONGODB_URI = config("MONGODB_URI", default=None)
MONGODB_DB_NAME = config("MONGODB_DB_NAME", default="veh_tpi")

if MONGODB_URI and not mongoengine.connection._connection_settings.get("default"):
    mongoengine.connect(db=MONGODB_DB_NAME, host=MONGODB_URI, alias="default")

from users.models import User
from stories.models import Scenario, Scene, Choice
from assets.models import Asset
from assets.services import (
    ImageGenerationService,
    SoundGenerationService,
    AssetStorageService,
)
from progress.models import PlayerProgress
import uuid


def get_or_create_admin():
    """Récupérer ou créer un utilisateur admin"""
    admin = User.objects(email="admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com",
            password="admin123",
            role="admin",
            first_name="Admin",
            last_name="User",
        )
        admin.save()
        print("✓ Admin créé: admin@example.com")
    else:
        print("✓ Admin existant trouvé: admin@example.com")
    return admin


def create_sample_users():
    """Créer des utilisateurs d'exemple"""
    print("Création des utilisateurs d'exemple...")

    # Admin
    admin_user = get_or_create_admin()

    # Joueur 1
    player1 = User.objects(email="player1@example.com").first()
    if not player1:
        player1 = User(
            email="player1@example.com",
            password="player123",
            role="player",
            first_name="Alice",
            last_name="Joueur",
        )
        player1.save()
        print(f"✓ Joueur créé: {player1.email}")
    else:
        print(f"✓ Joueur existant trouvé: {player1.email}")

    # Joueur 2
    player2 = User.objects(email="player2@example.com").first()
    if not player2:
        player2 = User(
            email="player2@example.com",
            password="player123",
            role="player",
            first_name="Bob",
            last_name="Joueur",
        )
        player2.save()
        print(f"✓ Joueur créé: {player2.email}")
    else:
        print(f"✓ Joueur existant trouvé: {player2.email}")

    return admin_user, player1, player2


def generate_image_asset(admin_user, title, description):
    """Générer une image via IA"""
    try:
        image_service = ImageGenerationService()
        storage_service = AssetStorageService()

        prompt = f"{title}. {description}"
        image_bytes, metadata = image_service.generate(prompt)

        extension = metadata.get("format", "png")
        filename = f"{uuid.uuid4()}.{extension}"
        url = storage_service.save_image(image_bytes, filename)

        mime_type_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }
        mime_type = mime_type_map.get(extension, "image/png")

        asset = Asset(
            type="image",
            name=f"Image générée: {title}",
            filename=filename,
            url=url,
            file_size=len(image_bytes),
            mime_type=mime_type,
            metadata=metadata,
            uploaded_by=admin_user,
            is_public=True,
        )
        asset.save()
        return asset
    except Exception as e:
        print(f"⚠️ Erreur génération image pour '{title}': {e}")
        return None


def generate_tts_asset(admin_user, title, text):
    """Générer un fichier TTS via IA"""
    try:
        sound_service = SoundGenerationService()
        storage_service = AssetStorageService()

        audio_bytes, metadata = sound_service.generate_text_to_speech(text, lang="fr")

        filename = f"{uuid.uuid4()}.mp3"
        url = storage_service.save_audio(audio_bytes, filename)

        asset = Asset(
            type="sound",
            name=f"Narration générée: {title}",
            filename=filename,
            url=url,
            file_size=len(audio_bytes),
            mime_type="audio/mpeg",
            metadata=metadata,
            uploaded_by=admin_user,
            is_public=True,
        )
        asset.save()
        return asset
    except Exception as e:
        print(f"⚠️ Erreur génération TTS pour '{title}': {e}")
        return None


def generate_music_asset(admin_user, title, description):
    """
    Générer une musique d'ambiance via IA

    ⚠️ NOTE: Les modèles MusicGen ne sont PAS disponibles via l'API d'inférence de Hugging Face.
    Cette fonction retournera None. Pour générer de la musique, il faut utiliser MusicGen localement
    ou via un autre service.
    """
    try:
        # Vérifier si le token Hugging Face est disponible
        from decouple import config

        hf_token = config("HUGGINGFACE_API_TOKEN", default=None)
        if not hf_token:
            print(
                f"   ⚠️ HUGGINGFACE_API_TOKEN non configuré - impossible de générer de la musique"
            )
            return None

        sound_service = SoundGenerationService()
        storage_service = AssetStorageService()

        music_description = f"musique d'ambiance pour: {description[:200]}"
        audio_bytes, metadata = sound_service.generate_ambient_music(
            music_description, duration=30
        )

        # Vérifier que les bytes audio sont valides
        if not audio_bytes or len(audio_bytes) < 100:
            raise Exception("Audio généré trop petit ou vide")

        filename = f"{uuid.uuid4()}.wav"
        url = storage_service.save_audio(audio_bytes, filename)

        asset = Asset(
            type="sound",
            name=f"Musique d'ambiance générée: {title}",
            filename=filename,
            url=url,
            file_size=len(audio_bytes),
            mime_type="audio/wav",
            metadata=metadata,
            uploaded_by=admin_user,
            is_public=True,
        )
        asset.save()
        return asset
    except Exception as e:
        error_msg = str(e)
        if "ne sont PAS disponibles" in error_msg:
            # Message court pour ne pas surcharger la sortie
            print(
                f"   ⚠️ Génération musique désactivée (MusicGen non disponible via l'API)"
            )
        else:
            print(f"   ⚠️ Erreur génération musique pour '{title}': {error_msg[:100]}")
        return None


def create_chateau_oublie_scenario(admin_user):
    """Créer le scénario complet 'Le Château Oublié'"""
    print("🏰 Création du scénario 'Le Château Oublié'...")
    print("=" * 60)

    # Vérifier si le scénario existe déjà
    existing_scenario = Scenario.objects(title="Le Château Oublié").first()
    if existing_scenario:
        print(
            f"⚠️ Le scénario 'Le Château Oublié' existe déjà (ID: {existing_scenario.id})"
        )
        print("   Suppression de l'ancien scénario...")
        existing_scenario.delete()
        print("✓ Scénario existant supprimé")

    # Créer le scénario
    scenario = Scenario(
        title="Le Château Oublié",
        description="Une aventure épique dans les ruines d'un ancien château rempli de mystères",
        author_id=admin_user,
        is_published=True,
    )
    scenario.save()
    print(f"✓ Scénario créé: {scenario.title}")

    # Définir les scènes avec leurs données
    scenes_data = [
        {
            "title": "L'entrée du château",
            "text": "Vous vous trouvez devant les ruines d'un ancien château. Les murs de pierre sont recouverts de lierre et de mousse. Une grande porte en bois se dresse devant vous, partiellement ouverte.",
            "order": 1,
            "is_start_scene": True,
            "is_end_scene": False,
            "auto_generate_image": True,
            "auto_generate_sound": True,
            "auto_generate_music": True,
        },
        {
            "title": "Le grand hall",
            "text": "Vous pénétrez dans un vaste hall aux plafonds voûtés. Des torches vacillantes projettent des ombres dansantes sur les murs de pierre. Des statues de chevaliers semblent vous observer depuis les recoins.",
            "order": 2,
            "is_start_scene": False,
            "is_end_scene": False,
            "auto_generate_image": True,
            "auto_generate_sound": True,
            "auto_generate_music": False,
        },
        {
            "title": "Les donjons souterrains",
            "text": "Vous descendez un escalier de pierre étroit et humide. L'air est froid et chargé d'humidité. Des gouttes d'eau résonnent dans l'obscurité, créant une atmosphère oppressante.",
            "order": 3,
            "is_start_scene": False,
            "is_end_scene": False,
            "auto_generate_image": False,
            "auto_generate_sound": False,
            "auto_generate_music": True,
        },
        {
            "title": "La bibliothèque secrète",
            "text": "Vous découvrez une bibliothèque secrète remplie de livres anciens. Des rayons de lumière filtrant par les fenêtres éclairent des étagères poussiéreuses. Des grimoires aux couvertures dorées semblent appeler votre attention.",
            "order": 4,
            "is_start_scene": False,
            "is_end_scene": False,
            "auto_generate_image": True,
            "auto_generate_sound": True,
            "auto_generate_music": False,
        },
        {
            "title": "La salle du trône",
            "text": "Vous pénétrez dans une immense salle du trône. Un trône en pierre imposant domine la pièce, entouré de bannières anciennes qui flottent dans l'air. Des échos lointains résonnent, créant une atmosphère à la fois majestueuse et inquiétante.",
            "order": 5,
            "is_start_scene": False,
            "is_end_scene": True,
            "auto_generate_image": True,
            "auto_generate_sound": True,
            "auto_generate_music": True,
        },
    ]

    # Créer les scènes
    scenes = []
    for scene_data in scenes_data:
        print(f"\n📖 Création de la scène: {scene_data['title']}")

        scene = Scene(
            scenario_id=scenario,
            title=scene_data["title"],
            text=scene_data["text"],
            order=scene_data["order"],
            is_start_scene=scene_data["is_start_scene"],
            is_end_scene=scene_data["is_end_scene"],
        )

        # Générer les assets si demandé
        if scene_data.get("auto_generate_image"):
            print("   🎨 Génération de l'image...")
            image_asset = generate_image_asset(
                admin_user, scene_data["title"], scene_data["text"]
            )
            if image_asset:
                scene.image_id = image_asset
                print("   ✓ Image générée")

        if scene_data.get("auto_generate_sound"):
            print("   🗣️ Génération du TTS...")
            tts_asset = generate_tts_asset(
                admin_user, scene_data["title"], scene_data["text"]
            )
            if tts_asset:
                scene.sound_id = tts_asset
                print("   ✓ TTS généré")

        if scene_data.get("auto_generate_music"):
            print("   🎵 Génération de la musique d'ambiance...")
            try:
                music_asset = generate_music_asset(
                    admin_user, scene_data["title"], scene_data["text"]
                )
                if music_asset:
                    scene.music_id = music_asset
                    print("   ✓ Musique générée")
            except Exception as e:
                error_msg = str(e)
                if "transformers" in error_msg.lower() or "torch" in error_msg.lower():
                    print(
                        f"   ⚠️ Bibliothèques manquantes: installez avec 'pip install transformers torch scipy numpy'"
                    )
                else:
                    print(f"   ⚠️ Erreur génération musique: {error_msg[:100]}")

        # Sauvegarder la scène et vérifier qu'elle a bien un ID
        scene.save()
        if not scene.id:
            raise Exception(f"Échec de sauvegarde de la scène: {scene.title}")

        scenes.append(scene)
        print(f"   ✓ Scène créée: {scene.title} (ID: {scene.id})")

    # Vérifier que toutes les scènes sont bien sauvegardées avant de créer les choices
    print("\n🔍 Vérification de la sauvegarde des scènes...")
    for i, scene in enumerate(scenes):
        scene.reload()
        if not scene.id:
            raise Exception(
                f"La scène '{scene.title}' n'a pas été sauvegardée correctement!"
            )
        print(f"   ✓ Scène {i+1} vérifiée: {scene.title}")

    # Définir les choices (liens entre scènes)
    choices_data = [
        {
            "from_scene": 0,  # L'entrée du château (scène 1)
            "to_scene": 1,  # Le grand hall (scène 2)
            "text": "Pénétrer dans le grand hall",
            "order": 1,
        },
        {
            "from_scene": 0,  # L'entrée du château (scène 1)
            "to_scene": 2,  # Les donjons souterrains (scène 3)
            "text": "Explorer les donjons",
            "order": 2,
        },
        {
            "from_scene": 1,  # Le grand hall (scène 2)
            "to_scene": 3,  # La bibliothèque secrète (scène 4)
            "text": "Chercher une bibliothèque",
            "order": 1,
        },
        {
            "from_scene": 2,  # Les donjons souterrains (scène 3)
            "to_scene": 4,  # La salle du trône (scène 5)
            "text": "Remonter vers la salle du trône",
            "order": 1,
        },
        {
            "from_scene": 3,  # La bibliothèque secrète (scène 4)
            "to_scene": 4,  # La salle du trône (scène 5)
            "text": "Sortir vers la salle du trône",
            "order": 1,
        },
    ]

    # Créer les choices
    print("\n🔗 Création des choices...")
    choices = []
    for choice_data in choices_data:
        from_scene = scenes[choice_data["from_scene"]]
        to_scene = scenes[choice_data["to_scene"]]

        choice = Choice(
            from_scene_id=from_scene,
            to_scene_id=to_scene,
            text=choice_data["text"],
            order=choice_data["order"],
        )
        choice.save()

        # Ajouter le choice à la scène source
        from_scene.choices.append(choice)
        from_scene.save()

        choices.append(choice)
        print(
            f"   ✓ Choice créé: '{choice_data['text']}' ({from_scene.title} → {to_scene.title})"
        )

    # Ajouter toutes les scènes au scénario et sauvegarder
    scenario.scenes = scenes
    scenario.save()

    # Recharger le scénario depuis la DB pour vérifier qu'il est bien sauvegardé
    scenario.reload()

    # Vérifier que le scénario est bien sauvegardé avec ses scènes
    if not scenario.id:
        raise Exception("Le scénario n'a pas été sauvegardé correctement!")

    print("\n🔍 Vérification finale de la sauvegarde...")
    print(f"   ✓ Scénario sauvegardé: {scenario.title} (ID: {scenario.id})")
    print(f"   ✓ Scénario contient {len(scenario.scenes)} scènes")

    # Compter les assets générés
    image_count = sum(1 for s in scenes if s.image_id)
    tts_count = sum(1 for s in scenes if s.sound_id)
    music_count = sum(1 for s in scenes if s.music_id)

    print(f"\n🎨 Assets générés :")
    print(f"   - {image_count} images")
    print(f"   - {tts_count} narrations (TTS)")
    print(f"   - {music_count} musiques d'ambiance")

    return scenario


def create_sample_progress(player1, player2, scenario):
    """Créer des progressions d'exemple (optionnel)"""
    print("\n📊 Création des progressions d'exemple (optionnel)...")

    # Vérifier si les progressions existent déjà
    progress1 = None
    progress2 = None

    # Progression pour player1
    existing_progress1 = PlayerProgress.objects(
        user_id=player1, scenario_id=scenario
    ).first()
    if not existing_progress1 and scenario.scenes and len(scenario.scenes) > 0:
        start_scene = scenario.scenes[0]  # Première scène (scène de début)
        progress1 = PlayerProgress(
            user_id=player1,
            scenario_id=scenario,
            current_scene_id=start_scene,
            total_time_spent=0,
        )
        progress1.save()
        print(f"✓ Progression créée pour {player1.email}")
    elif existing_progress1:
        print(f"✓ Progression existante trouvée pour {player1.email}")

    # Progression pour player2
    existing_progress2 = PlayerProgress.objects(
        user_id=player2, scenario_id=scenario
    ).first()
    if not existing_progress2 and scenario.scenes and len(scenario.scenes) > 0:
        start_scene = scenario.scenes[0]  # Première scène (scène de début)
        progress2 = PlayerProgress(
            user_id=player2,
            scenario_id=scenario,
            current_scene_id=start_scene,
            total_time_spent=0,
        )
        progress2.save()
        print(f"✓ Progression créée pour {player2.email}")
    elif existing_progress2:
        print(f"✓ Progression existante trouvée pour {player2.email}")

    return progress1, progress2


def main():
    """Fonction principale du script de peuplement"""
    print("🌱 Début du peuplement des données d'exemple...")
    print("=" * 60)

    try:
        # Créer les utilisateurs
        admin_user, player1, player2 = create_sample_users()

        # Créer le scénario "Le Château Oublié"
        scenario = create_chateau_oublie_scenario(admin_user)

        # Créer les progressions (optionnel)
        progress1, progress2 = create_sample_progress(player1, player2, scenario)

        print("\n" + "=" * 60)
        print("✅ Peuplement terminé avec succès !")
        print("\n📊 Résumé :")
        print(f"   - {User.objects.count()} utilisateurs")
        print(f"   - {Asset.objects.count()} assets")
        print(f"   - {Scenario.objects.count()} scénario")
        print(f"   - {Scene.objects.count()} scènes")
        print(f"   - {Choice.objects.count()} choix")
        print(f"   - {PlayerProgress.objects.count()} progressions")

        print("\n🔑 Identifiants de connexion :")
        print("   Admin: admin@example.com / admin123")
        print("   Joueur 1: player1@example.com / player123")
        print("   Joueur 2: player2@example.com / player123")

        print(f"\n📝 IDs importants :")
        print(f"   - Scénario ID: {scenario.id}")
        if scenario.scenes:
            print(f"   - Scène de début ID: {scenario.scenes[0].id}")
            print(f"   - Scène de fin ID: {scenario.scenes[-1].id}")

        print("\n🌐 Accès à l'API :")
        print("   GraphQL Playground: http://localhost:8000/graphql/")
        print("   JWT Endpoints: http://localhost:8000/graphql-jwt/")

        print(f"\n🌐 Pour tester dans l'application mobile :")
        print(f"   Utilisez le scenarioId: {scenario.id}")

    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du peuplement : {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
