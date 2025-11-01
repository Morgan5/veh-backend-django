import graphene
from graphene_mongo import MongoengineObjectType
from users.models import User
import os
import jwt
from datetime import datetime, timedelta


class UserType(MongoengineObjectType):
    """
    Type GraphQL pour le modèle User
    """

    mongo_id = graphene.String()

    class Meta:
        model = User
        fields = (
            "id",
            "mongo_id",
            "email",
            "role",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_mongo_id(parent, info):
        return str(parent.id)


class CreateUserInput(graphene.InputObjectType):
    """
    Input pour créer un utilisateur
    """

    email = graphene.String(required=True)
    password = graphene.String(required=True)
    role = graphene.String(default_value="player")
    first_name = graphene.String()
    last_name = graphene.String()


class UpdateUserInput(graphene.InputObjectType):
    """
    Input pour mettre à jour un utilisateur
    """

    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    role = graphene.String()


class CreateUser(graphene.Mutation):
    """
    Mutation pour créer un utilisateur
    """

    class Arguments:
        input = CreateUserInput(required=True)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            # Vérifier si l'email existe déjà
            if User.objects(email=input.email).first():
                return CreateUser(
                    user=None,
                    success=False,
                    message="Un utilisateur avec cet email existe déjà",
                )

            # Créer l'utilisateur
            user = User(
                email=input.email,
                password=input.password,  # Sera hashé automatiquement
                role=input.role,
                first_name=input.first_name,
                last_name=input.last_name,
            )
            user.save()

            return CreateUser(
                user=user, success=True, message="Utilisateur créé avec succès"
            )
        except Exception as e:
            return CreateUser(user=None, success=False, message=str(e))


class UpdateUser(graphene.Mutation):
    """
    Mutation pour mettre à jour un utilisateur
    """

    class Arguments:
        user_id = graphene.ID(required=True)
        input = UpdateUserInput(required=True)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, user_id, input):
        user = get_user_from_context(info)
        if user:
            try:
                user = User.objects(id=user_id).first()
                if not user:
                    return UpdateUser(
                        user=None, success=False, message="Utilisateur non trouvé"
                    )

                # Mettre à jour les champs
                if input.email:
                    user.email = input.email
                if input.first_name:
                    user.first_name = input.first_name
                if input.last_name:
                    user.last_name = input.last_name
                if input.role:
                    user.role = input.role

                user.save()

                return UpdateUser(
                    user=user,
                    success=True,
                    message="Utilisateur mis à jour avec succès",
                )
            except Exception as e:
                return UpdateUser(user=None, success=False, message=str(e))
        raise Exception("You do not have permission to perform this action")


class DeleteUser(graphene.Mutation):
    """
    Mutation pour supprimer un utilisateur
    """

    class Arguments:
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, user_id):
        user = get_user_from_context(info)
        if user:
            try:
                user = User.objects(id=user_id).first()
                if not user:
                    return DeleteUser(success=False, message="Utilisateur non trouvé")

                user.delete()

                return DeleteUser(
                    success=True, message="Utilisateur supprimé avec succès"
                )
            except Exception as e:
                return DeleteUser(success=False, message=str(e))
        raise Exception("You do not have permission to perform this action")


class Query(graphene.ObjectType):
    """
    Queries pour l'application users
    """

    all_users = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, user_id=graphene.ID(required=True))
    user_by_email = graphene.Field(UserType, email=graphene.String(required=True))
    me = graphene.Field(UserType)

    def resolve_all_users(self, info):
        """Récupérer tous les utilisateurs"""
        user = get_user_from_context(info)
        if user and user.is_admin:
            return User.objects.all()
        raise Exception("You do not have permission to perform this action")

    def resolve_user_by_id(self, info, user_id):
        """Récupérer un utilisateur par ID"""
        user = get_user_from_context(info)
        if user and (user.is_admin or str(user.id) == user_id):
            return User.objects(id=user_id).first()
        return None

    def resolve_user_by_email(self, info, email):
        """Récupérer un utilisateur par email"""
        user = get_user_from_context(info)
        if user and user.is_admin:
            return User.objects(email=email).first()
        return None

    def resolve_me(self, info):
        """Récupérer l'utilisateur connecté"""
        user = get_user_from_context(info)
        return user


class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, email, password):
        user = User.objects(email=email).first()
        if not user or not user.check_password(password):
            return Login(success=False, message="Email ou mot de passe invalide")

        # Crée un token JWT personnalisé (à adapter selon ton usage)
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        secret_key = os.getenv("SECRET_KEY", "dev-secret")
        token = jwt.encode(payload, secret_key, algorithm="HS256")

        return Login(token=token, success=True, message="Connexion réussie")


class Mutation(graphene.ObjectType):
    """
    Mutations pour l'application users
    """

    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    login = Login.Field()


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
