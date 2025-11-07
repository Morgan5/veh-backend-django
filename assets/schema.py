import graphene
from graphene_mongo import MongoengineObjectType
from .models import Asset
import os
import jwt
from users.models import User


class AssetType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle Asset
    """

    mongo_id = graphene.String()
    file_size_mb = graphene.Float()
    file_extension = graphene.String()
    dimensions = graphene.String()
    duration = graphene.String()

    class Meta:
        model = Asset
        fields = "__all__"
        interfaces = (graphene.relay.Node,)

    def resolve_file_size_mb(self, info):
        """Obtenir la taille en MB"""
        return self.get_file_size_mb()

    def resolve_file_extension(self, info):
        """Obtenir l'extension du fichier"""
        return self.get_file_extension()

    def resolve_dimensions(self, info):
        """Obtenir les dimensions pour les images/vidéos"""
        return self.get_dimensions()

    def resolve_duration(self, info):
        """Obtenir la durée pour les sons/vidéos"""
        return self.get_duration()

    def resolve_mongo_id(parent, info):
        return str(parent.id)


# Input types
class CreateAssetInput(graphene.InputObjectType):
    type = graphene.String(required=True)
    name = graphene.String(required=True)
    filename = graphene.String(required=True)
    url = graphene.String(required=True)
    file_size = graphene.Int()
    mime_type = graphene.String()
    metadata = graphene.JSONString()
    is_public = graphene.Boolean(default_value=True)


class UpdateAssetInput(graphene.InputObjectType):
    name = graphene.String()
    url = graphene.String()
    metadata = graphene.JSONString()
    is_public = graphene.Boolean()


# Mutations
class CreateAsset(graphene.Mutation):
    """
    Mutation pour créer un asset
    """

    class Arguments:
        input = CreateAssetInput(required=True)

    asset = graphene.Field(AssetType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        try:
            # Vérifier que le type est valide
            valid_types = [choice[0] for choice in Asset.ASSET_TYPES]
            if input.type not in valid_types:
                return CreateAsset(
                    asset=None,
                    success=False,
                    message=f"Type d'asset invalide. Types valides: {', '.join(valid_types)}",
                )

            asset = Asset(
                type=input.type,
                name=input.name,
                filename=input.filename,
                url=input.url,
                file_size=input.file_size,
                mime_type=input.mime_type,
                metadata=input.metadata or {},
                uploaded_by=user,
                is_public=input.is_public,
            )
            asset.save()

            return CreateAsset(
                asset=asset, success=True, message="Asset créé avec succès"
            )
        except Exception as e:
            return CreateAsset(asset=None, success=False, message=str(e))


class UpdateAsset(graphene.Mutation):
    """
    Mutation pour mettre à jour un asset
    """

    class Arguments:
        asset_id = graphene.ID(required=True)
        input = UpdateAssetInput(required=True)

    asset = graphene.Field(AssetType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, asset_id, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        try:
            asset = Asset.objects(id=asset_id).first()

            if not asset:
                return UpdateAsset(
                    asset=None, success=False, message="Asset non trouvé"
                )

            if input.name:
                asset.name = input.name
            if input.url:
                asset.url = input.url
            if input.metadata is not None:
                asset.metadata = input.metadata
            if input.is_public is not None:
                asset.is_public = input.is_public

            asset.save()

            return UpdateAsset(
                asset=asset, success=True, message="Asset mis à jour avec succès"
            )
        except Exception as e:
            return UpdateAsset(asset=None, success=False, message=str(e))


class DeleteAsset(graphene.Mutation):
    """
    Mutation pour supprimer un asset
    """

    class Arguments:
        asset_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, asset_id):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        try:
            asset = Asset.objects(id=asset_id).first()

            if not asset:
                return DeleteAsset(success=False, message="Asset non trouvé")

            # Supprimer le fichier physique et l'asset de la base
            success, message = delete_asset_with_file(asset)

            return DeleteAsset(success=success, message=message)
        except Exception as e:
            return DeleteAsset(success=False, message=str(e))


class GenerateAsset(graphene.Mutation):
    """
    Mutation pour générer un asset via IA
    - Images : générées via Hugging Face Stable Diffusion à partir de descriptions
    - Sons : générés via gTTS (Text-to-Speech) pour la narration ou Hugging Face MusicGen pour la musique d'ambiance
    """

    class Arguments:
        type = graphene.String(required=True)
        name = graphene.String(required=True)
        description = graphene.String()
        # Options spécifiques selon le type
        sound_type = (
            graphene.String()
        )  # Pour les sons : 'tts' (narration) ou 'music' (ambiance). Défaut: 'tts'
        language = graphene.String()  # Pour les sons TTS (défaut: 'fr')
        duration = graphene.Int()  # Pour la musique d'ambiance (défaut: 30)

    asset = graphene.Field(AssetType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(
        self,
        info,
        type,
        name,
        description=None,
        sound_type=None,
        language=None,
        duration=None,
    ):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        try:
            # Vérifier que le type est valide
            valid_types = [choice[0] for choice in Asset.ASSET_TYPES]
            if type not in valid_types:
                return GenerateAsset(
                    asset=None,
                    success=False,
                    message=f"Type d'asset invalide. Types valides: {', '.join(valid_types)}",
                )

            # Vérifier qu'une description est fournie
            if not description:
                return GenerateAsset(
                    asset=None,
                    success=False,
                    message="Une description est requise pour générer l'asset",
                )

            from .services import (
                ImageGenerationService,
                SoundGenerationService,
                AssetStorageService,
            )
            import uuid
            import os

            storage_service = AssetStorageService()

            if type == "image":
                # Générer une image via Hugging Face
                image_service = ImageGenerationService()
                image_bytes, metadata = image_service.generate(description)

                # Générer un nom de fichier unique
                extension = metadata.get("format", "png")
                filename = f"{uuid.uuid4()}.{extension}"

                # Sauvegarder l'image
                url = storage_service.save_image(image_bytes, filename)

                # Déterminer le MIME type
                mime_type_map = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "webp": "image/webp",
                }
                mime_type = mime_type_map.get(extension, "image/png")

                # Créer l'asset
                asset = Asset(
                    type=type,
                    name=name,
                    filename=filename,
                    url=url,
                    file_size=len(image_bytes),
                    mime_type=mime_type,
                    metadata=metadata,
                    uploaded_by=user,
                    is_public=True,
                )

            elif type == "sound":
                # Déterminer le type de son : TTS (narration) ou musique d'ambiance
                # Par défaut, utiliser TTS pour la narration
                sound_type_param = sound_type or "tts"

                # Validation du type de son
                if sound_type_param not in ["tts", "music"]:
                    return GenerateAsset(
                        asset=None,
                        success=False,
                        message=f"Type de son invalide. Types valides: 'tts' (narration), 'music' (musique d'ambiance)",
                    )

                sound_service = SoundGenerationService()

                if sound_type_param == "tts":
                    # Générer de la narration (Text-to-Speech)
                    # description = le texte à narrer
                    lang = language or "fr"
                    audio_bytes, metadata = sound_service.generate_text_to_speech(
                        description, lang=lang
                    )
                    extension = "mp3"
                    mime_type = "audio/mpeg"
                    asset_name_prefix = "Narration"
                else:  # sound_type_param == 'music'
                    # Générer de la musique d'ambiance
                    # description = description de l'ambiance musicale (ex: "musique sombre et inquiétante")
                    duration_sec = duration or 30
                    audio_bytes, metadata = sound_service.generate_ambient_music(
                        description, duration=duration_sec
                    )
                    extension = "wav"  # MusicGen génère du WAV
                    mime_type = "audio/wav"
                    asset_name_prefix = "Musique d'ambiance"

                # Générer un nom de fichier unique
                filename = f"{uuid.uuid4()}.{extension}"

                # Sauvegarder l'audio
                url = storage_service.save_audio(audio_bytes, filename)

                # Créer l'asset avec un nom plus descriptif si le nom fourni est générique
                asset_name = (
                    name if name else f"{asset_name_prefix}: {description[:50]}"
                )

                # Créer l'asset
                asset = Asset(
                    type=type,
                    name=asset_name,
                    filename=filename,
                    url=url,
                    file_size=len(audio_bytes),
                    mime_type=mime_type,
                    metadata=metadata,
                    uploaded_by=user,
                    is_public=True,
                )

            elif type == "video":
                # Pour les vidéos, on peut générer une image animée ou une vidéo simple
                # Pour l'instant, on retourne une erreur car la génération vidéo est complexe
                return GenerateAsset(
                    asset=None,
                    success=False,
                    message="La génération de vidéos n'est pas encore implémentée",
                )

            else:
                return GenerateAsset(
                    asset=None,
                    success=False,
                    message=f"Type d'asset non supporté pour la génération: {type}",
                )

            asset.save()

            return GenerateAsset(
                asset=asset,
                success=True,
                message=f"Asset {type} généré avec succès via IA",
            )

        except ValueError as e:
            # Erreur de configuration (ex: token manquant)
            return GenerateAsset(
                asset=None, success=False, message=f"Erreur de configuration: {str(e)}"
            )
        except Exception as e:
            return GenerateAsset(
                asset=None,
                success=False,
                message=f"Erreur lors de la génération: {str(e)}",
            )


# Queries
class Query(graphene.ObjectType):
    """
    Queries pour l'application assets
    """

    all_assets = graphene.List(AssetType, type_filter=graphene.String())
    asset_by_id = graphene.Field(AssetType, asset_id=graphene.ID(required=True))
    assets_by_type = graphene.List(AssetType, type=graphene.String(required=True))
    assets_by_uploader = graphene.List(
        AssetType, uploader_id=graphene.ID(required=True)
    )
    my_assets = graphene.List(AssetType)
    public_assets = graphene.List(AssetType, type_filter=graphene.String())

    def resolve_all_assets(self, info, type_filter=None):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        """Récupérer tous les assets"""
        assets = Asset.objects.all()

        if type_filter:
            assets = assets.filter(type=type_filter)

        return assets

    def resolve_asset_by_id(self, info, asset_id):
        """Récupérer un asset par ID"""
        return Asset.objects(id=asset_id).first()

    def resolve_assets_by_type(self, info, type):
        """Récupérer les assets par type"""
        return Asset.objects(type=type)

    def resolve_assets_by_uploader(self, info, uploader_id):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        """Récupérer les assets d'un uploader"""
        return Asset.objects(uploaded_by=uploader_id)

    def resolve_my_assets(self, info):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        """Récupérer les assets de l'utilisateur connecté"""
        return Asset.objects(uploaded_by=user)

    def resolve_public_assets(self, info, type_filter=None):
        """Récupérer les assets publics"""
        assets = Asset.objects(is_public=True)
        if type_filter:
            assets = assets.filter(type=type_filter)
        return assets


class Mutation(graphene.ObjectType):
    """
    Mutations pour l'application assets
    """

    create_asset = CreateAsset.Field()
    update_asset = UpdateAsset.Field()
    delete_asset = DeleteAsset.Field()
    generate_asset = GenerateAsset.Field()


def get_user_from_context(info):
    auth = info.context.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("JWT "):
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(
                token, os.getenv("SECRET_KEY", "dev-secret"), algorithms=["HS256"]
            )
            user = User.objects(id=payload["user_id"]).first()
            return user
        except Exception:
            return None
    return None


def delete_asset_with_file(asset):
    """
    Supprime un asset de la base de données et son fichier physique
    
    Args:
        asset: Instance d'Asset à supprimer
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Supprimer le fichier physique si l'asset a un filename
        if asset and asset.filename:
            from .services import AssetStorageService
            storage_service = AssetStorageService()
            storage_service.delete_file(asset.filename)
        
        # Supprimer l'asset de la base de données
        if asset:
            asset.delete()
        
        return True, "Asset supprimé avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression de l'asset: {str(e)}"