import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import login_required
from .models import Scenario, Scene, Choice
import os
import jwt
from users.models import User

class ScenarioType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle Scenario
    """
    mongo_id = graphene.String()

    class Meta:
        model = Scenario
        fields = '__all__'
        interfaces = (graphene.relay.Node,)

    def resolve_mongo_id(parent, info):
        return str(parent.id)


class SceneType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle Scene
    """
    mongo_id = graphene.String()

    class Meta:
        model = Scene
        fields = '__all__'
        interfaces = (graphene.relay.Node,)

    def resolve_mongo_id(parent, info):
        return str(parent.id)


class ChoiceType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle Choice
    """
    mongo_id = graphene.String()

    class Meta:
        model = Choice
        fields = '__all__'
        interfaces = (graphene.relay.Node,)

    def resolve_mongo_id(parent, info):
        return str(parent.id)


# Input types
class CreateScenarioInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String()
    is_published = graphene.Boolean(default_value=False)


class UpdateScenarioInput(graphene.InputObjectType):
    title = graphene.String()
    description = graphene.String()
    is_published = graphene.Boolean()


class CreateSceneInput(graphene.InputObjectType):
    scenario_id = graphene.ID(required=True)
    title = graphene.String(required=True)
    text = graphene.String(required=True)
    order = graphene.Int(default_value=0)
    image_id = graphene.ID()
    sound_id = graphene.ID()
    is_start_scene = graphene.Boolean(default_value=False)
    is_end_scene = graphene.Boolean(default_value=False)
    # Option pour générer automatiquement les assets via IA
    auto_generate_image = graphene.Boolean(default_value=False)
    auto_generate_sound = graphene.Boolean(default_value=False)


class UpdateSceneInput(graphene.InputObjectType):
    title = graphene.String()
    text = graphene.String()
    order = graphene.Int()
    image_id = graphene.ID()
    sound_id = graphene.ID()
    is_start_scene = graphene.Boolean()
    is_end_scene = graphene.Boolean()


class CreateChoiceInput(graphene.InputObjectType):
    from_scene_id = graphene.ID(required=True)
    to_scene_id = graphene.ID(required=True)
    text = graphene.String(required=True)
    condition = graphene.JSONString()
    order = graphene.Int(default_value=0)


class UpdateChoiceInput(graphene.InputObjectType):
    to_scene_id = graphene.ID()
    text = graphene.String()
    condition = graphene.JSONString()
    order = graphene.Int()


# Mutations
class CreateScenario(graphene.Mutation):
    """
    Mutation pour créer un scénario
    """
    class Arguments:
        input = CreateScenarioInput(required=True)
    
    scenario = graphene.Field(ScenarioType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        try:
            scenario = Scenario(
                title=input.title,
                description=input.description,
                author_id=user,
                is_published=input.is_published
            )
            scenario.save()
            
            return CreateScenario(
                scenario=scenario,
                success=True,
                message="Scénario créé avec succès"
            )
        except Exception as e:
            return CreateScenario(
                scenario=None,
                success=False,
                message=str(e)
            )


class UpdateScenario(graphene.Mutation):
    """
    Mutation pour mettre à jour un scénario
    """
    class Arguments:
        scenario_id = graphene.ID(required=True)
        input = UpdateScenarioInput(required=True)
    
    scenario = graphene.Field(ScenarioType)
    success = graphene.Boolean()
    message = graphene.String()
    

    def mutate(self, info, scenario_id, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")

        try:
            scenario = Scenario.objects(id=scenario_id).first()
            
            if not scenario:
                return UpdateScenario(
                    scenario=None,
                    success=False,
                    message="Scénario non trouvé"
                )
            
            if input.title:
                scenario.title = input.title
            if input.description is not None:
                scenario.description = input.description
            if input.is_published is not None:
                scenario.is_published = input.is_published
            
            scenario.save()
            
            return UpdateScenario(
                scenario=scenario,
                success=True,
                message="Scénario mis à jour avec succès"
            )
        except Exception as e:
            return UpdateScenario(
                scenario=None,
                success=False,
                message=str(e)
            )


class CreateScene(graphene.Mutation):
    """
    Mutation pour créer une scène
    """
    class Arguments:
        input = CreateSceneInput(required=True)
    
    scene = graphene.Field(SceneType)
    success = graphene.Boolean()
    message = graphene.String()
 
    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        try:
            scenario = Scenario.objects(id=input.scenario_id).first()
            
            if not scenario:
                return CreateScene(
                    scene=None,
                    success=False,
                    message="Scénario non trouvé"
                )
            
            scene = Scene(
                scenario_id=scenario,
                title=input.title,
                text=input.text,
                order=input.order,
                is_start_scene=input.is_start_scene,
                is_end_scene=input.is_end_scene
            )
            
            # Ajouter les assets si fournis manuellement
            if input.image_id:
                from assets.models import Asset
                scene.image_id = Asset.objects(id=input.image_id).first()
            if input.sound_id:
                from assets.models import Asset
                scene.sound_id = Asset.objects(id=input.sound_id).first()
            
            # Génération automatique d'assets via IA si demandé
            if input.auto_generate_image and not scene.image_id:
                try:
                    from assets.services import ImageGenerationService, AssetStorageService
                    from assets.models import Asset
                    import uuid
                    
                    image_service = ImageGenerationService()
                    storage_service = AssetStorageService()
                    
                    # Utiliser le texte de la scène comme prompt pour l'image
                    prompt = f"{input.title}. {input.text}"
                    image_bytes, metadata = image_service.generate(prompt)
                    
                    extension = metadata.get('format', 'png')
                    filename = f"{uuid.uuid4()}.{extension}"
                    url = storage_service.save_image(image_bytes, filename)
                    
                    mime_type_map = {
                        'png': 'image/png',
                        'jpg': 'image/jpeg',
                        'jpeg': 'image/jpeg',
                        'webp': 'image/webp'
                    }
                    mime_type = mime_type_map.get(extension, 'image/png')
                    
                    image_asset = Asset(
                        type='image',
                        name=f"Image générée: {input.title}",
                        filename=filename,
                        url=url,
                        file_size=len(image_bytes),
                        mime_type=mime_type,
                        metadata=metadata,
                        uploaded_by=user,
                        is_public=True
                    )
                    image_asset.save()
                    scene.image_id = image_asset
                    
                except Exception as e:
                    # Si la génération échoue, on continue sans l'image
                    # (on pourrait logger l'erreur ici)
                    pass
            
            if input.auto_generate_sound and not scene.sound_id:
                try:
                    from assets.services import SoundGenerationService, AssetStorageService
                    from assets.models import Asset
                    import uuid
                    
                    sound_service = SoundGenerationService()
                    storage_service = AssetStorageService()
                    
                    # Utiliser le texte de la scène pour générer un son TTS
                    audio_bytes, metadata = sound_service.generate_text_to_speech(
                        input.text, 
                        lang='fr'
                    )
                    
                    filename = f"{uuid.uuid4()}.mp3"
                    url = storage_service.save_audio(audio_bytes, filename)
                    
                    sound_asset = Asset(
                        type='sound',
                        name=f"Son généré: {input.title}",
                        filename=filename,
                        url=url,
                        file_size=len(audio_bytes),
                        mime_type='audio/mpeg',
                        metadata=metadata,
                        uploaded_by=user,
                        is_public=True
                    )
                    sound_asset.save()
                    scene.sound_id = sound_asset
                    
                except Exception as e:
                    # Si la génération échoue, on continue sans le son
                    pass
            
            scene.save()
            
            # Ajouter la scène au scénario
            scenario.scenes.append(scene)
            scenario.save()
            
            return CreateScene(
                scene=scene,
                success=True,
                message="Scène créée avec succès"
            )
        except Exception as e:
            return CreateScene(
                scene=None,
                success=False,
                message=str(e)
            )


class CreateChoice(graphene.Mutation):
    """
    Mutation pour créer un choix
    """
    class Arguments:
        input = CreateChoiceInput(required=True)
    
    choice = graphene.Field(ChoiceType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        
        try:
            from_scene = Scene.objects(id=input.from_scene_id).first()
            to_scene = Scene.objects(id=input.to_scene_id).first()
            
            if not from_scene or not to_scene:
                return CreateChoice(
                    choice=None,
                    success=False,
                    message="Scène source ou destination non trouvée"
                )
            
            choice = Choice(
                from_scene_id=from_scene,
                to_scene_id=to_scene,
                text=input.text,
                condition=input.condition,
                order=input.order
            )
            choice.save()
            
            # Ajouter le choix à la scène source
            from_scene.choices.append(choice)
            from_scene.save()
            
            return CreateChoice(
                choice=choice,
                success=True,
                message="Choix créé avec succès"
            )
        except Exception as e:
            return CreateChoice(
                choice=None,
                success=False,
                message=str(e)
            )


# Queries
class Query(graphene.ObjectType):
    """
    Queries pour l'application stories
    """
    all_scenarios = graphene.List(ScenarioType, published_only=graphene.Boolean(default_value=False))
    scenario_by_id = graphene.Field(ScenarioType, scenario_id=graphene.ID(required=True))
    scenarios_by_author = graphene.List(ScenarioType, author_id=graphene.ID(required=True))
    scene_by_id = graphene.Field(SceneType, scene_id=graphene.ID(required=True))
    scenes_by_scenario = graphene.List(SceneType, scenario_id=graphene.ID(required=True))
    choice_by_id = graphene.Field(ChoiceType, choice_id=graphene.ID(required=True))
    choices_by_scene = graphene.List(ChoiceType, scene_id=graphene.ID(required=True))
    
    def resolve_all_scenarios(self, info, published_only=False):
        """Récupérer tous les scénarios"""
        if published_only:
            return Scenario.objects(is_published=True)
        return Scenario.objects.all()
    
    def resolve_scenario_by_id(self, info, scenario_id):
        """Récupérer un scénario par ID"""
        return Scenario.objects(id=scenario_id).first()
    
    def resolve_scenarios_by_author(self, info, author_id):
        """Récupérer les scénarios d'un auteur"""
        return Scenario.objects(author_id=author_id)
    
    def resolve_scene_by_id(self, info, scene_id):
        """Récupérer une scène par ID"""
        return Scene.objects(id=scene_id).first()
    
    def resolve_scenes_by_scenario(self, info, scenario_id):
        """Récupérer les scènes d'un scénario"""
        return Scene.objects(scenario_id=scenario_id).order_by('order')
    
    def resolve_choice_by_id(self, info, choice_id):
        """Récupérer un choix par ID"""
        return Choice.objects(id=choice_id).first()
    
    def resolve_choices_by_scene(self, info, scene_id):
        """Récupérer les choix d'une scène"""
        return Choice.objects(from_scene_id=scene_id).order_by('order')


class Mutation(graphene.ObjectType):
    """
    Mutations pour l'application stories
    """
    create_scenario = CreateScenario.Field()
    update_scenario = UpdateScenario.Field()
    create_scene = CreateScene.Field()
    create_choice = CreateChoice.Field() 


def get_user_from_context(info):
    auth = info.context.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("JWT "):
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, os.getenv("SECRET_KEY", "dev-secret"), algorithms=["HS256"])
            user = User.objects(id=payload["user_id"]).first()
            return user
        except Exception:
            return None
    return None