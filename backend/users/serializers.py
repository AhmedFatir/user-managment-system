from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
	@classmethod
	def get_token(cls, user):
		token = super().get_token(user)
		token['username'] = user.username
		return token


class LoginSerializer(serializers.Serializer):
	username = serializers.CharField()
	password = serializers.CharField()

	def get_user(self, data):
		user = authenticate(username=data['username'], password=data['password'])
		return user


class RegisterSerializer(serializers.ModelSerializer):
	password2 = serializers.CharField(write_only=True, required=True)

	class Meta:
		model = User
		fields = ('username', 'email', 'password', 'password2')

	def validate(self, attrs):
		if attrs['password'] != attrs['password2']:
			raise serializers.ValidationError({"password": "Password fields didn't match."})
		return attrs

	def validate_email(self, value):
		if User.objects.filter(email=value).exists():
			raise serializers.ValidationError("A user with this email already exists.")
		return value

	def validate_username(self, value):
		if User.objects.filter(username=value).exists():
			raise serializers.ValidationError("A user with this username already exists.")
		return value

	def create(self, validated_data):
		user = User.objects.create_user(
			username=validated_data['username'],
			email=validated_data['email'],
			password=validated_data['password']
		)
		return user


class PasswordChangeSerializer(serializers.Serializer):
	old_password = serializers.CharField(required=True)
	new_password = serializers.CharField(required=True)

	def validate_new_password(self, value):
		password_validation.validate_password(value)
		return value

	def validate_old_password(self, value):
		user = self.context['request'].user
		if not user.check_password(value):
			raise serializers.ValidationError("Old password is not correct")
		return value

	def save(self, **kwargs):
		password = self.validated_data['new_password']
		user = self.context['request'].user
		user.set_password(password)
		user.save()
		return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ['username', 'email', 'first_name', 'last_name']

	def validate_email(self, value):
		user = self.context['request'].user
		if User.objects.exclude(pk=user.pk).filter(email=value).exists():
			raise serializers.ValidationError("This email is already in use.")
		return value

	def validate_username(self, value):
		user = self.context['request'].user
		if User.objects.exclude(pk=user.pk).filter(username=value).exists():
			raise serializers.ValidationError("This username is already in use.")
		return value

	def update(self, instance, validated_data):
		instance.username = validated_data.get('username', instance.username)
		instance.email = validated_data.get('email', instance.email)
		instance.first_name = validated_data.get('first_name', instance.first_name)
		instance.last_name = validated_data.get('last_name', instance.last_name)
		instance.save()
		return instance

class PasswordResetSerializer(serializers.Serializer):
	email = serializers.EmailField()

	def validate_email(self, value):
		if not User.objects.filter(email=value).exists():
			raise serializers.ValidationError("User with this email address does not exist.")
		return value


class UserAvatarSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ['avatar']

	def update(self, instance, validated_data):
		if 'avatar' in validated_data:
			instance.avatar = validated_data['avatar']
			instance.save()
		return instance


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = [
			'id', 'intra_id', 'username', 'email','first_name', 'last_name', 
			'avatar', 'is_2fa_enabled', 'is_online', 'date_joined', 'last_login',
			'friends', 'incoming_requests', 'outgoing_requests', 'blocked_users'
		]
		read_only_fields = ['id', 'date_joined', 'last_login']
		def get_avatar(self, obj):
			if obj.avatar:
				return self.context['request'].build_absolute_uri(obj.avatar.url)
			return None

