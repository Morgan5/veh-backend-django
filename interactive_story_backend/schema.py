import graphene
#from graphene_django.debug import DjangoDebug
import graphql_jwt

# Import des schémas des applications
from users.schema import Query as UsersQuery, Mutation as UsersMutation
from stories.schema import Query as StoriesQuery, Mutation as StoriesMutation
from progress.schema import Query as ProgressQuery, Mutation as ProgressMutation
from assets.schema import Query as AssetsQuery, Mutation as AssetsMutation


class Query(
    UsersQuery,
    StoriesQuery,
    ProgressQuery,
    AssetsQuery,
    graphene.ObjectType
):
    """
    Schéma GraphQL principal - Query
    Combine toutes les queries des différentes applications
    """
    #debug = graphene.Field(DjangoDebug, name='__debug')
    pass


class Mutation(
    UsersMutation,
    StoriesMutation,
    ProgressMutation,
    AssetsMutation,
    graphene.ObjectType
):
    """
    Schéma GraphQL principal - Mutation
    Combine toutes les mutations des différentes applications
    """
    tokenAuth = graphql_jwt.ObtainJSONWebToken.Field()
    verifyToken = graphql_jwt.Verify.Field()
    refreshToken = graphql_jwt.Refresh.Field()
    pass


# Schéma GraphQL principal
schema = graphene.Schema(query=Query, mutation=Mutation) 