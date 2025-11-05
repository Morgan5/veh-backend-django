from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
import os
import uuid
import jwt
from PIL import Image
from users.models import User
from .services import AssetStorageService
from .models import Asset


def get_user_from_request(request):
    """Extract user from JWT token in request header"""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("JWT "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token, os.getenv("SECRET_KEY", "dev-secret"), algorithms=["HS256"]
            )
            user = User.objects(id=payload["user_id"]).first()
            return user
        except Exception:
            return None
    return None


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])  # Vérification manuelle via JWT
def upload_file(request):
    """
    Endpoint REST pour uploader un fichier
    Accepte FormData avec :
    - file: le fichier à uploader
    - type: "image" | "sound" | "video"
    - name: nom de l'asset (optionnel)
    - scene_id: ID de la scène à laquelle lier l'asset (optionnel)
    - asset_field: "image_id" | "sound_id" | "music_id" (optionnel, requis si scene_id fourni)
    
    Retourne :
    - filename: nom du fichier sauvegardé
    - url: URL relative du fichier
    - fileSize: taille du fichier
    - mimeType: type MIME
    - metadata: métadonnées (dimensions pour images, etc.)
    - scene: informations sur la scène liée (si scene_id fourni)
    """
    # Vérifier l'authentification
    user = get_user_from_request(request)
    if not user:
        return JsonResponse(
            {"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # Vérifier que le fichier est présent
    if "file" not in request.FILES:
        return JsonResponse(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES["file"]
    asset_type = request.POST.get("type", "image")
    asset_name = request.POST.get("name", file.name)

    # Valider le type
    valid_types = ["image", "sound", "video"]
    if asset_type not in valid_types:
        return JsonResponse(
            {"error": f"Invalid type. Valid types: {', '.join(valid_types)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        storage_service = AssetStorageService()

        # Générer un nom de fichier unique
        file_extension = os.path.splitext(file.name)[1] or ".bin"
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Lire le contenu du fichier
        file_content = file.read()

        # Sauvegarder le fichier
        if asset_type == "image":
            url = storage_service.save_image(file_content, unique_filename)
        elif asset_type == "sound" or asset_type == "video":
            url = storage_service.save_audio(file_content, unique_filename)
        else:
            # Pour les autres types, utiliser save_audio comme méthode générique
            url = storage_service.save_audio(file_content, unique_filename)

        # Extraire les métadonnées
        metadata = {}
        mime_type = file.content_type or "application/octet-stream"

        # Métadonnées pour les images
        if asset_type == "image":
            try:
                filepath = os.path.join(storage_service.media_root, unique_filename)
                image = Image.open(filepath)
                width, height = image.size
                metadata = {
                    "width": width,
                    "height": height,
                    "format": image.format.lower() if image.format else "unknown",
                }
            except Exception:
                pass

        # Créer l'entrée dans MongoDB
        asset = Asset(
            type=asset_type,
            name=asset_name,
            filename=unique_filename,
            url=url,
            file_size=len(file_content),
            mime_type=mime_type,
            metadata=metadata,
            uploaded_by=user,
            is_public=request.POST.get("is_public", "true").lower() == "true",
        )
        asset.save()

        # Lier l'asset à une scène si scene_id fourni
        scene_id = request.POST.get("scene_id")
        asset_field = request.POST.get("asset_field")  # "image_id", "sound_id", "music_id"
        linked_scene = None

        if scene_id:
            from stories.models import Scene
            
            # Récupérer la scène
            scene = Scene.objects(id=scene_id).first()
            
            if not scene:
                return JsonResponse(
                    {"error": f"Scène non trouvée avec l'ID: {scene_id}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Vérifier que l'utilisateur est l'auteur du scénario
            if str(scene.scenario_id.author_id.id) != str(user.id):
                return JsonResponse(
                    {"error": "Vous n'avez pas la permission de modifier cette scène"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            # Déterminer le champ à utiliser
            if not asset_field:
                # Auto-détection basée sur le type d'asset
                if asset_type == "image":
                    asset_field = "image_id"
                elif asset_type == "sound":
                    asset_field = "sound_id"  # Par défaut sound_id pour les sons
                else:
                    asset_field = "sound_id"  # Pour les vidéos aussi
            
            # Valider le champ
            valid_fields = ["image_id", "sound_id", "music_id"]
            if asset_field not in valid_fields:
                return JsonResponse(
                    {"error": f"Champ invalide. Champs valides: {', '.join(valid_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Lier l'asset à la scène
            setattr(scene, asset_field, asset)
            scene.save()
            linked_scene = scene

        # Préparer la réponse
        response_data = {
            "success": True,
            "message": "Fichier uploadé et asset créé avec succès",
            "asset": {
                "id": str(asset.id),
                "mongoId": str(asset.id),
                "type": asset.type,
                "name": asset.name,
                "filename": asset.filename,
                "url": asset.url,
                "fullUrl": f"{request.scheme}://{request.get_host()}{asset.url}",
                "fileSize": asset.file_size,
                "fileSizeMb": asset.get_file_size_mb(),
                "mimeType": asset.mime_type,
                "metadata": asset.metadata,
                "isPublic": asset.is_public,
                "createdAt": asset.created_at.isoformat() if asset.created_at else None,
            },
        }

        # Ajouter les infos de la scène si liée
        if linked_scene:
            response_data["message"] = "Fichier uploadé, asset créé et lié à la scène avec succès"
            response_data["scene"] = {
                "id": str(linked_scene.id),
                "mongoId": str(linked_scene.id),
                "title": linked_scene.title,
                "assetField": asset_field,
            }

        return JsonResponse(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
