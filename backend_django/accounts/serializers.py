from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Inject custom claims into the JWT payload
        user_role = getattr(user, 'profile', None)
        token['role'] = user_role.role if user_role else 'CUSTOMER'
        token['username'] = user.username

        return token