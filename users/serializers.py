from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'date_joined',
            'totp_enabled', 'theme', 'language', 'currency',
            'email_notifications', 'telegram_notifications',
            'notify_large_expense', 'notify_budget_exceeded', 'notify_daily_summary',
            'telegram_user_id', 'telegram_username'
        )
        read_only_fields = ('id', 'date_joined', 'totp_enabled', 'telegram_user_id', 'telegram_username')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PreferencesSerializer(serializers.ModelSerializer):
    """Serializer для налаштувань теми, мови, валюти."""

    class Meta:
        model = User
        fields = ('theme', 'language', 'currency')


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer для налаштувань повідомлень."""

    class Meta:
        model = User
        fields = (
            'email_notifications', 'telegram_notifications',
            'notify_large_expense', 'notify_budget_exceeded', 'notify_daily_summary'
        )


class TOTPSetupSerializer(serializers.Serializer):
    """Serializer для повернення QR коду та секрету TOTP."""
    qr_code = serializers.CharField()
    secret = serializers.CharField()


class TOTPEnableSerializer(serializers.Serializer):
    """Serializer для активації TOTP."""
    code = serializers.CharField(max_length=6, min_length=6)
    secret = serializers.CharField(max_length=32)


class TOTPDisableSerializer(serializers.Serializer):
    """Serializer для вимкнення TOTP."""
    password = serializers.CharField()


class TOTPVerifySerializer(serializers.Serializer):
    """Serializer для верифікації TOTP коду."""
    code = serializers.CharField(max_length=6, min_length=6)
