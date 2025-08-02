import graphene
from graphene_mongo import MongoengineObjectType
from .models import PlayerProgress, HistoryEntry
import os
import jwt
from users.models import User

class HistoryEntryType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle HistoryEntry
    """
    mongo_id = graphene.String()

    class Meta:
        model = HistoryEntry
        fields = '__all__'

    def resolve_mongo_id(parent, info):
        return str(parent.id)

class PlayerProgressType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle PlayerProgress
    """
    progress_percentage = graphene.Float()
    mongo_id = graphene.String()
    
    class Meta:
        model = PlayerProgress
        fields = '__all__'
        interfaces = (graphene.relay.Node,)
    
    def resolve_progress_percentage(self, info):
        """Calculer le pourcentage de progression"""
        return self.get_progress_percentage()
    
    def resolve_mongo_id(parent, info):
        return str(parent.id)


# Input types
class CreateProgressInput(graphene.InputObjectType):
    scenario_id = graphene.ID(required=True)
    current_scene_id = graphene.ID(required=True)


class RecordProgressInput(graphene.InputObjectType):
    progress_id = graphene.ID(required=True)
    scene_id = graphene.ID(required=True)
    choice_id = graphene.ID()
    metadata = graphene.JSONString()


class UpdateProgressInput(graphene.InputObjectType):
    current_scene_id = graphene.ID()
    total_time_spent = graphene.Int()


# Mutations
class CreateProgress(graphene.Mutation):
    """
    Mutation pour créer une progression de joueur
    """
    class Arguments:
        input = CreateProgressInput(required=True)
    
    progress = graphene.Field(PlayerProgressType)
    success = graphene.Boolean()
    message = graphene.String()
 
    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        
        try:
            from stories.models import Scenario, Scene
            
            scenario = Scenario.objects(id=input.scenario_id).first()
            scene = Scene.objects(id=input.current_scene_id).first()
            
            if not scenario:
                return CreateProgress(
                    progress=None,
                    success=False,
                    message="Scénario non trouvé"
                )
            
            if not scene:
                return CreateProgress(
                    progress=None,
                    success=False,
                    message="Scène non trouvée"
                )
            
            # Vérifier si une progression existe déjà
            existing_progress = PlayerProgress.objects(
                user_id=user,
                scenario_id=scenario
            ).first()
            
            if existing_progress:
                return CreateProgress(
                    progress=existing_progress,
                    success=True,
                    message="Progression existante récupérée"
                )
            
            # Créer une nouvelle progression
            progress = PlayerProgress(
                user_id=user,
                scenario_id=scenario,
                current_scene_id=scene
            )
            progress.save()
            
            return CreateProgress(
                progress=progress,
                success=True,
                message="Progression créée avec succès"
            )
        except Exception as e:
            return CreateProgress(
                progress=None,
                success=False,
                message=str(e)
            )


class RecordProgress(graphene.Mutation):
    """
    Mutation pour enregistrer un choix de progression
    """
    class Arguments:
        input = RecordProgressInput(required=True)
    
    progress = graphene.Field(PlayerProgressType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        
        try:
            from stories.models import Scene, Choice
            
            progress = PlayerProgress.objects(id=input.progress_id).first()
            scene = Scene.objects(id=input.scene_id).first()
            choice = None
            
            if input.choice_id:
                choice = Choice.objects(id=input.choice_id).first()
            
            if not progress:
                return RecordProgress(
                    progress=None,
                    success=False,
                    message="Progression non trouvée"
                )
            
            if not scene:
                return RecordProgress(
                    progress=None,
                    success=False,
                    message="Scène non trouvée"
                )
            
            # Déplacer vers la nouvelle scène
            progress.move_to_scene(scene, choice, input.metadata)
            
            return RecordProgress(
                progress=progress,
                success=True,
                message="Progression enregistrée avec succès"
            )
        except Exception as e:
            return RecordProgress(
                progress=None,
                success=False,
                message=str(e)
            )


class UpdateProgress(graphene.Mutation):
    """
    Mutation pour mettre à jour une progression
    """
    class Arguments:
        progress_id = graphene.ID(required=True)
        input = UpdateProgressInput(required=True)
    
    progress = graphene.Field(PlayerProgressType)
    success = graphene.Boolean()
    message = graphene.String()
  
    def mutate(self, info, progress_id, input):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        
        try:
            from stories.models import Scene
            
            progress = PlayerProgress.objects(id=progress_id).first()
            
            if not progress:
                return UpdateProgress(
                    progress=None,
                    success=False,
                    message="Progression non trouvée"
                )
            
            if input.current_scene_id:
                scene = Scene.objects(id=input.current_scene_id).first()
                if scene:
                    progress.current_scene_id = scene
            
            if input.total_time_spent is not None:
                progress.total_time_spent = input.total_time_spent
            
            progress.save()
            
            return UpdateProgress(
                progress=progress,
                success=True,
                message="Progression mise à jour avec succès"
            )
        except Exception as e:
            return UpdateProgress(
                progress=None,
                success=False,
                message=str(e)
            )


class DeleteProgress(graphene.Mutation):
    """
    Mutation pour supprimer une progression
    """
    class Arguments:
        progress_id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, progress_id):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        try:
            progress = PlayerProgress.objects(id=progress_id).first()
            
            if not progress:
                return DeleteProgress(
                    success=False,
                    message="Progression non trouvée"
                )
            
            progress.delete()
            
            return DeleteProgress(
                success=True,
                message="Progression supprimée avec succès"
            )
        except Exception as e:
            return DeleteProgress(
                success=False,
                message=str(e)
            )


# Queries
class Query(graphene.ObjectType):
    """
    Queries pour l'application progress
    """
    all_progress = graphene.List(PlayerProgressType)
    progress_by_id = graphene.Field(PlayerProgressType, progress_id=graphene.ID(required=True))
    progress_by_user = graphene.List(PlayerProgressType, user_id=graphene.ID(required=True))
    progress_by_scenario = graphene.List(PlayerProgressType, scenario_id=graphene.ID(required=True))
    my_progress = graphene.List(PlayerProgressType)
    progress_by_user_and_scenario = graphene.Field(
        PlayerProgressType, 
        user_id=graphene.ID(required=True),
        scenario_id=graphene.ID(required=True)
    )
 
    def resolve_all_progress(self, info):
        """Récupérer toutes les progressions (admin seulement)"""
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        return PlayerProgress.objects.all()
    
    def resolve_progress_by_id(self, info, progress_id):
        """Récupérer une progression par ID"""
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        progress = PlayerProgress.objects(id=progress_id).first()

        if progress:
            return progress
        return None
    
    def resolve_progress_by_user(self, info, user_id):
        """Récupérer les progressions d'un utilisateur"""
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        return PlayerProgress.objects(user_id=user_id)
    
    def resolve_progress_by_scenario(self, info, scenario_id):
        """Récupérer les progressions d'un scénario (admin seulement)"""
        # Cette query nécessite des droits admin pour la confidentialité
        return []
  
    def resolve_my_progress(self, info):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        """Récupérer les progressions de l'utilisateur connecté"""
        return PlayerProgress.objects(user_id=user)
    
    def resolve_progress_by_user_and_scenario(self, info, user_id, scenario_id):
        user = get_user_from_context(info)
        if not user:
            raise Exception("Authentication required")
        """Récupérer la progression d'un utilisateur pour un scénario spécifique"""
        return PlayerProgress.objects(
                user_id=user_id,
                scenario_id=scenario_id
            ).first()


class Mutation(graphene.ObjectType):
    """
    Mutations pour l'application progress
    """
    create_progress = CreateProgress.Field()
    record_progress = RecordProgress.Field()
    update_progress = UpdateProgress.Field()
    delete_progress = DeleteProgress.Field() 


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