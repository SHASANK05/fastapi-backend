from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Inject role and username into the JWT payload
        user_profile = getattr(user, "profile", None)
        token["role"] = user_profile.role if user_profile else "CUSTOMER"
        token["username"] = user.username

        return token

    def validate(self, attrs):
        # Include role and user details directly in the login JSON response
        data = super().validate(attrs)
        user_profile = getattr(self.user, "profile", None)
        role = user_profile.role if user_profile else "CUSTOMER"

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": role,
        }
        return data


class LoginView(TokenObtainPairView):
    """
    Subclasses SimpleJWT TokenObtainPairView using our custom serializer.
    Returns access, refresh tokens, and user metadata with roles.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = getattr(request.user, "profile", None)
        role = user_profile.role if user_profile else "CUSTOMER"

        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "role": role,
            },
            status=status.HTTP_200_OK,
        )