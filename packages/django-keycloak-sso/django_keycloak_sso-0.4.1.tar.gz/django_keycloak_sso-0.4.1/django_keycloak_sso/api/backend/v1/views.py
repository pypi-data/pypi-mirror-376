from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django_keycloak_sso.api import serializers as module_serializers
from django_keycloak_sso.base_views import BaseKeycloakAdminView
from django_keycloak_sso.documentation import keycloak_login_doc, keycloak_api_doc, keycloak_admin_doc
from django_keycloak_sso.keycloak import KeyCloakConfidentialClient
from django_keycloak_sso.paginations import DefaultPagination
from django_keycloak_sso.sso.authentication import CustomUser
from ...serializers import (KeyCloakSetCookieSerializer,
                            GroupCreateSerializer,
                            AssignRoleGroupManySerializer,
                            UserJoinGroupSerializer,
                            TokenRequestSerializer
                            )


class KeyCloakLoginView(APIView):
    http_method_names = ('post',)
    authentication_classes = []

    @keycloak_login_doc(
        operation_summary="Set Token Cookie",
        operation_description="Set received token from keycloak on request cookie",
        request_body=KeyCloakSetCookieSerializer,
        responses={
            200: {
                'description': 'Login successful',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'message': {'type': 'string'},
                                'token': {'type': 'string'},
                                'user': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    )
    def post(self, request: Request) -> Response:
        keycloak_klass = KeyCloakConfidentialClient()
        serializer = KeyCloakSetCookieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        refresh_token = serializer.validated_data['refreshToken']
        client_id = serializer.validated_data['client_id']

        try:
            decoded_token = keycloak_klass.decode_token(token)
        except KeyCloakConfidentialClient.KeyCloakException as e:
            return Response({"error": str(e)}, status=401)

        response = Response({
            "message": "Login successful",
            "token": token,
            "user": decoded_token
        }, status=status.HTTP_200_OK)

        if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
            response = keycloak_klass.set_httponly_cookie('access_token', token, response)
            response = keycloak_klass.set_httponly_cookie('refresh_token', refresh_token, response)
            response = keycloak_klass.set_httponly_cookie('client_id', client_id, response)

        return response


class KeyCloakRefreshView(APIView):
    authentication_classes = []

    @keycloak_api_doc(
        operation_summary="Refresh Token",
        operation_description="Refresh received token from keycloak",
        responses={
            200: {
                'description': 'Token refreshed successfully',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'},
                                'access_token': {'type': 'string', 'description': 'New access token'},
                                'refresh_token': {'type': 'string', 'description': 'New refresh token (optional)'}
                            }
                        }
                    }
                }
            },
            401: {
                'description': 'No refresh token or client ID / Token refresh failed',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        keycloak_klass = KeyCloakConfidentialClient()
        refresh_token = keycloak_klass.get_token(request, 'refresh_token')
        client_id = keycloak_klass.get_token(request, 'client_id')

        if not refresh_token or not client_id:
            return Response({"detail": "No refresh token Or Client ID"}, status=401)

        try:
            new_tokens = keycloak_klass.send_request(
                keycloak_klass.KeyCloakRequestTypeChoices.REFRESH_ACCESS_TOKEN,
                keycloak_klass.KeyCloakRequestTypeChoices,
                keycloak_klass.KeyCloakRequestMethodChoices.POST,
                keycloak_klass.KeyCloakPanelTypeChoices.USER,
                refresh_token=refresh_token,
                client_id=client_id,
            )
        except Exception as e:
            return Response({"detail": "Token refresh failed"}, status=401)

        response = Response({"detail": "Token refreshed"}, status=200)
        response.set_cookie("access_token", new_tokens["access_token"], httponly=True, secure=True)

        if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
            response = keycloak_klass.set_httponly_cookie('refresh_token', refresh_token, response)
            if "refresh_token" in new_tokens:
                response.set_cookie("refresh_token", new_tokens["refresh_token"], httponly=True, secure=True)
            return response

        return Response(new_tokens, status=200)


class KeyCloakLogoutView(APIView):
    authentication_classes = []

    @keycloak_api_doc(
        operation_summary="Logout Token",
        operation_description="Logout received token from keycloak",
        responses={
            200: {
                'description': 'Logged out successfully',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string', 'example': 'Logged out'}
                            }
                        }
                    }
                }
            },
            401: {
                'description': 'No refresh token or client ID',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        keycloak_klass = KeyCloakConfidentialClient()
        refresh_token = keycloak_klass.get_token(request, 'refresh_token')
        client_id = keycloak_klass.get_token(request, 'client_id')

        if not refresh_token or not client_id:
            return Response({"detail": "No refresh token Or Client ID"}, status=401)

        logout_res = keycloak_klass.send_request(
            keycloak_klass.KeyCloakRequestTypeChoices.LOGOUT,
            keycloak_klass.KeyCloakRequestTypeChoices,
            keycloak_klass.KeyCloakRequestMethodChoices.POST,
            keycloak_klass.KeyCloakPanelTypeChoices.USER,
            refresh_token=refresh_token,
            client_id=client_id,
        )

        if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
            response = Response({"detail": "Logged out"}, status=200)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            response.delete_cookie("client_id")
            return response

        return Response({"detail": "Logged out"}, status=200)


class UserProfileRetrieveView(BaseKeycloakAdminView):

    @keycloak_admin_doc(
        operation_summary="User Profile Retrieve",
        operation_description="User Profile Retrieve from keycloak",
        responses={
            200: module_serializers.UserSerializer(),
            401: {
                'description': 'Invalid or expired token',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request: Request):
        keycloak_klass = KeyCloakConfidentialClient()
        access_token = keycloak_klass.get_token(request, 'access_token')

        try:
            decoded_token = keycloak_klass.decode_token(access_token)
        except KeyCloakConfidentialClient.KeyCloakException as e:
            return Response({"error": str(e)}, status=401)

        return Response(module_serializers.UserSerializer(
            CustomUser(payload=decoded_token, is_authenticated=False)
        ).data, status=200)


class GroupListRetrieveView(BaseKeycloakAdminView):
    pagination_class = DefaultPagination

    @keycloak_admin_doc(
        operation_summary="Group List Retrieve",
        operation_description="Group List Retrieve from keycloak",
        responses={
            200: module_serializers.GroupSerializer(many=True),
            404: {
                'description': 'Requested group data was not found',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        parameters=[
            {
                'name': 'own',
                'in': 'query',
                'description': 'Filter to user\'s own groups (set to "1" to enable)',
                'required': False,
                'schema': {'type': 'string', 'enum': ['1']}
            },
            {
                'name': 'type',
                'in': 'query',
                'description': 'Filter groups by type/role',
                'required': False,
                'schema': {'type': 'string'}
            }
        ]
    )
    def get(self, request: Request, pk: str = None):
        keycloak_klass = KeyCloakConfidentialClient()

        try:
            response = keycloak_klass.send_request(
                keycloak_klass.KeyCloakRequestTypeChoices.GROUPS,
                keycloak_klass.KeyCloakRequestTypeChoices,
                keycloak_klass.KeyCloakRequestMethodChoices.GET,
                keycloak_klass.KeyCloakPanelTypeChoices.ADMIN,
                detail_pk=pk,
            )


            if response is None:
                response = []
            elif not isinstance(response, list):
                response = [response]

            if request.query_params.get("own") == "1" and not pk:
                user_group_names = [group for group in request.user.groups_parent]
                response = [group for group in response if group.get("name") in user_group_names]

                group_type = request.query_params.get("type")
                if group_type:
                    group_with_type = [
                        user_group for user_group in request.user.groups_dict_list
                        if user_group.get("role") == group_type
                    ]
                    group_with_type_name_list = [group.get("title") for group in group_with_type]
                    response = [group for group in response if group.get("name") in group_with_type_name_list]

            serializer = module_serializers.GroupSerializer(response, many=True)

            if isinstance(response, list) and len(response) > 0:
                paginator = self.pagination_class()
                paginated_queryset = paginator.paginate_queryset(response, request)
                serializer = module_serializers.GroupSerializer(paginated_queryset, many=True)
                return paginator.get_paginated_response(serializer.data)

            return Response(serializer.data)

        except keycloak_klass.KeyCloakNotFoundException:
            return Response({"detail": "Requested group data was not found"}, status=404)


def find_group_id(groups, search_name):
    """
    get group ID
    """
    for group in groups:
        if group.get("name") == search_name:
            return group.get("id")
        sub_groups = group.get("subGroups") or []
        if sub_groups:
            result = find_group_id(sub_groups, search_name)
            if result:
                return result
    return None


class FindGroupIDView(APIView):
    """
    Get detail group by group name
    """

    def find_group_detailing(self , detailing_type , group_name):
        keycloak = KeyCloakConfidentialClient()

        extra_params = {'extra_query_params': {'search': group_name}}

        try:
            groups = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.GROUPS,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.GET,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                **extra_params
            )

            if detailing_type == 'id':
                group_id = find_group_id(groups, group_name)
                response = {"id": group_id}
            else:
                response = groups

            return {'response':response,
                    'status': 200
                    }

        except Exception as e:

            return {"detail": "Group name not found",
                    "error": str(e),
                    "status": 404
                    }


    @keycloak_admin_doc(
        operation_summary="Group Retrieve",
        operation_description="Group Retrieve from keycloak by group name.",

        # Add query parameters documentation
        parameters=[
            {
                'name': 'detailing_type',
                'in': 'query',
                'description': 'How to display group information',
                'required': True,
                'schema': {
                    'type': 'string',
                    'enum':['id','detail']
                },
            }
        ]
    )
    def get(self, request, *args, **kwargs):

        request_param = request.query_params.get('detailing_type')

        group_name = kwargs.get('group_name')


        result = self.find_group_detailing(request_param,group_name)

        if result.get('status') == 200:
            return Response(result.get('response'),status.HTTP_200_OK)

        else:
            return Response(
                {"detail": result.get('detail'), "error": result.get('error')},
                status=status.HTTP_404_NOT_FOUND)



class UserListRetrieveView(BaseKeycloakAdminView):

    @keycloak_admin_doc(
        operation_summary="User List Retrieve",
        operation_description="User List Retrieve from keycloak",
        responses={
            200: {
                'description': 'List of users from KeyCloak',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'description': 'User data from KeyCloak'
                            }
                        }
                    }
                }
            },
            404: {
                'description': 'Requested user data was not found',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request: Request, pk: str = None):
        keycloak_klass = KeyCloakConfidentialClient()

        try:
            response = keycloak_klass.send_request(
                keycloak_klass.KeyCloakRequestTypeChoices.USERS,
                keycloak_klass.KeyCloakRequestTypeChoices,
                keycloak_klass.KeyCloakRequestMethodChoices.GET,
                keycloak_klass.KeyCloakPanelTypeChoices.ADMIN,
                detail_pk=pk,
            )
        except keycloak_klass.KeyCloakNotFoundException as e:
            return Response({"detail": "Requested user data was not found"}, status=404)

        return Response(response, status=200)


class CreateGroupView(APIView):
    serializer_class = GroupCreateSerializer

    @keycloak_admin_doc(
        operation_summary="Create group",
        operation_description='Create a group. '
                               'Optional: You can create a group '
                              'in that subcategory by passing the group ID in the parameter',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': {
                    'detail': 'Created group successfully',
                    'response': 'object'
                }
            }
        },
        parameters=[
            {
                'name': 'group_parent_id',
                'in': 'query',
                'description': 'Enter the group ID above of the branch.',
                'required': False,
                'schema': {'type': 'string'}
            }
        ]
    )
    def post(self, request, *args, **kwargs):
        srz_data = self.serializer_class(data=request.data)
        srz_data.is_valid(raise_exception=True)

        group_parent_id = request.query_params.get('group_parent_id')

        group_name = srz_data.validated_data['name']

        keycloak = KeyCloakConfidentialClient()

        try:
            response = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.GROUPS,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.POST,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                name=group_name,
                group_parent_id=group_parent_id
            )
            return Response({'detail':'Created group successfully',
                             'response':response},status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteGroupView(APIView):
    """
    deleting group by group id
    """

    def deleting_group(self , group_id):
        keycloak = KeyCloakConfidentialClient()

        try:
            response = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.GROUPS,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.DELETE,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                group_id=group_id
            )
            return {'detail':'Group successfully deleted.',
                    'response':response,
                    'status':200
                    }

        except Exception as e:
            return {"detail": str(e),'status': 404}

    @keycloak_admin_doc(
        operation_summary="Delete group",
        operation_description='Deleting group by Group ID.',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': {
                    'detail': 'Group successfully deleted.',
                    'response': 'object'
                }
            }
        }
    )
    def delete(self,request, *args , **kwargs):
        group_id = kwargs.get('group_id')
        result = self.deleting_group(group_id)
        return Response({'detail':result.get('detail')},result.get('status'))


class RoleListRetrieveView(APIView):
    """
    List and Retrieve roles
    """

    @keycloak_admin_doc(
        operation_summary="Role List and Retrieve",
        operation_description="List and details of a client's roles",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': {
                    'detail': 'Request successful.'
                }
            }
        }
    )
    def get(self, request , role_id=None):

        keycloak = KeyCloakConfidentialClient()
        try:
            response = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.CLIENT_ROLES,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.GET,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                role_id=role_id
            )
            return Response(response,status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AssignRoleGroupView(APIView):
    """
    assigning roles to group
    """
    serializer_class = AssignRoleGroupManySerializer

    @keycloak_admin_doc(
        operation_summary="Assigning role to group",
        operation_description="Assign a role to the desired group",
        request_body = AssignRoleGroupManySerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': {
                    'detail': 'Request successful.'
                }
            }
        }
    )
    def post(self,request, pk):
        srz_data = self.serializer_class(data=request.data)
        srz_data.is_valid(raise_exception=True)
        roles = srz_data.validated_data

        keycloak = KeyCloakConfidentialClient()

        try:
            response = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.ASSIGN_ROLE_GROUP,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.POST,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                group_id=pk,
                roles=roles
            )

            return Response(response,status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserJoinGroupView(APIView):
    serializer_class = UserJoinGroupSerializer

    @keycloak_admin_doc(
        operation_summary="User join to group",
        operation_description="User join to group",
        request_body = UserJoinGroupSerializer,
        responses={
            204: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': {
                    'detail': 'Request successful.'
                }
            }
        }
    )
    def post(self, request):
        srz_data = self.serializer_class(data=request.data)
        srz_data.is_valid(raise_exception=True)

        user_id = srz_data.validated_data.get('user_id')
        group_id = srz_data.validated_data.get('group_id')

        keycloak = KeyCloakConfidentialClient()

        try:
            response = keycloak.send_request(
                keycloak.KeyCloakRequestTypeChoices.USER_JOIN_GROUP,
                keycloak.KeyCloakRequestTypeChoices,
                keycloak.KeyCloakRequestMethodChoices.PUT,
                keycloak.KeyCloakPanelTypeChoices.ADMIN,
                user_id=user_id,
                group_id=group_id
            )

            return Response(response)
        except Exception as e:
            return Response({'detail': str(e)}, status.HTTP_400_BAD_REQUEST)


class FrontAPIView(APIView):


    @keycloak_api_doc(
        operation_summary="Create Token",
        operation_description="Create token for given user",
        request_body = TokenRequestSerializer,
        responses={
            204: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                },
                'example': "string"
            }
        }
    )
    def post(self, request):
        keycloak_klass = KeyCloakConfidentialClient()
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            access_key = keycloak_klass.send_request(
                keycloak_klass.KeyCloakRequestTypeChoices.PASSWORD_ACCESS_TOKEN,
                keycloak_klass.KeyCloakRequestTypeChoices,
                keycloak_klass.KeyCloakRequestMethodChoices.POST,
                keycloak_klass.KeyCloakPanelTypeChoices.USER,
                username=username,
                password=password,
            )
        except keycloak_klass.KeyCloakException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(access_key, status=status.HTTP_200_OK)

