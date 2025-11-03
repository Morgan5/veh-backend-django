#!/usr/bin/env python3
"""
Script pour vider complètement la base MongoDB.
Supprime toutes les collections dans l'ordre approprié pour respecter les références.

Usage:
    python fixtures/clear_database.py
    ou
    python manage.py shell < fixtures/clear_database.py
"""

import os
import sys
import django

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
from progress.models import PlayerProgress


def clear_database():
    """Vider toutes les collections MongoDB dans l'ordre approprié"""
    print("🗑️  Vidage de la base de données MongoDB...")
    print("=" * 60)

    counts = {}

    # Supprimer les documents qui référencent d'autres documents en premier
    # 1. PlayerProgress (référence User, Scenario, Scene, Choice)
    print("\n📊 Suppression des progressions des joueurs...")
    count = PlayerProgress.objects.count()
    PlayerProgress.objects.all().delete()
    counts["PlayerProgress"] = count
    print(f"   ✓ {count} progressions supprimées")

    # 2. Choice (référence Scene)
    print("\n🔗 Suppression des choices...")
    count = Choice.objects.count()
    Choice.objects.all().delete()
    counts["Choice"] = count
    print(f"   ✓ {count} choices supprimés")

    # 3. Scene (référence Scenario, Asset)
    print("\n📖 Suppression des scènes...")
    count = Scene.objects.count()
    Scene.objects.all().delete()
    counts["Scene"] = count
    print(f"   ✓ {count} scènes supprimées")

    # 4. Scenario (référence User)
    print("\n📚 Suppression des scénarios...")
    count = Scenario.objects.count()
    Scenario.objects.all().delete()
    counts["Scenario"] = count
    print(f"   ✓ {count} scénarios supprimés")

    # 5. Asset (référence User)
    print("\n🎨 Suppression des assets...")
    count = Asset.objects.count()
    Asset.objects.all().delete()
    counts["Asset"] = count
    print(f"   ✓ {count} assets supprimés")

    # 6. User (peut être supprimé en dernier)
    print("\n👤 Suppression des utilisateurs...")
    count = User.objects.count()
    User.objects.all().delete()
    counts["User"] = count
    print(f"   ✓ {count} utilisateurs supprimés")

    print("\n" + "=" * 60)
    print("✅ Base de données vidée avec succès !")
    print("\n📊 Résumé des suppressions :")
    for model_name, count in counts.items():
        print(f"   - {model_name}: {count} documents supprimés")

    total = sum(counts.values())
    print(f"\n   Total: {total} documents supprimés")

    # Vérification finale
    print("\n🔍 Vérification finale...")
    remaining_users = User.objects.count()
    remaining_scenarios = Scenario.objects.count()
    remaining_scenes = Scene.objects.count()
    remaining_choices = Choice.objects.count()
    remaining_assets = Asset.objects.count()
    remaining_progress = PlayerProgress.objects.count()

    if (
        remaining_users == 0
        and remaining_scenarios == 0
        and remaining_scenes == 0
        and remaining_choices == 0
        and remaining_assets == 0
        and remaining_progress == 0
    ):
        print("   ✓ Toutes les collections sont vides")
    else:
        print("   ⚠️ ATTENTION: Certaines collections ne sont pas vides!")
        if remaining_users > 0:
            print(f"      - Users: {remaining_users}")
        if remaining_scenarios > 0:
            print(f"      - Scenarios: {remaining_scenarios}")
        if remaining_scenes > 0:
            print(f"      - Scenes: {remaining_scenes}")
        if remaining_choices > 0:
            print(f"      - Choices: {remaining_choices}")
        if remaining_assets > 0:
            print(f"      - Assets: {remaining_assets}")
        if remaining_progress > 0:
            print(f"      - PlayerProgress: {remaining_progress}")


def main():
    """Fonction principale"""
    try:
        # Demander confirmation
        print(
            "⚠️  ATTENTION: Cette opération va supprimer TOUTES les données de la base MongoDB!"
        )
        response = input("Êtes-vous sûr de vouloir continuer ? (o/N): ")

        if response.lower() != "o":
            print("❌ Opération annulée")
            sys.exit(0)

        clear_database()

        print(
            "\n🎉 Base de données vidée ! Vous pouvez maintenant exécuter seed_data.py pour peupler la base."
        )

    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du vidage : {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
