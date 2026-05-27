from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

TRACKING_SOURCE_CHOICES = {
    'cash',
    'card',
    'bank',
    'wallet',
    'savings',
    'all',
}


class TrackingSourcesValidatorMixin:
    def validate_tracking_sources(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError('Оберіть хоча б одне джерело відстеження.')

        invalid = [item for item in value if item not in TRACKING_SOURCE_CHOICES]
        if invalid:
            raise serializers.ValidationError('Містить недозволені джерела відстеження.')

        return list(dict.fromkeys(value))


class UserRegSerializer(serializers.ModelSerializer, TrackingSourcesValidatorMixin):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    display_currency = serializers.ChoiceField(choices=User.CURRENCY_CHOICES, required=False)
    tracking_sources = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(TRACKING_SOURCE_CHOICES)),
        allow_empty=False,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'language',
            'currency',
            'display_currency',
            'theme',
            'tracking_sources',
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        display_currency = validated_data.pop('display_currency', None) or validated_data.get('currency', 'UAH')
        tracking_sources = validated_data.pop('tracking_sources', [])
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            display_currency=display_currency,
            tracking_sources=tracking_sources,
            onboarding_completed=True,
            **validated_data,
        )
        return user


class TelegramRegisterSerializer(UserRegSerializer):
    telegram_user_id = serializers.IntegerField(min_value=1, write_only=True)
    telegram_username = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )

    class Meta(UserRegSerializer.Meta):
        fields = UserRegSerializer.Meta.fields + (
            'telegram_user_id',
            'telegram_username',
        )

    def create(self, validated_data):
        validated_data.pop('telegram_user_id', None)
        validated_data.pop('telegram_username', None)
        return super().create(validated_data)


class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'date_joined')


class PrivateProfileSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'date_joined',
            'totp_enabled',
            'theme',
            'language',
            'currency',
            'display_currency',
            'tracking_sources',
            'onboarding_completed',
            'email_notifications',
            'telegram_notifications',
            'notify_large_expense',
            'notify_budget_exceeded',
            'notify_daily_summary',
            'telegram_user_id',
            'telegram_username',
        )
        read_only_fields = (
            'id',
            'date_joined',
            'totp_enabled',
            'telegram_user_id',
            'telegram_username',
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PreferencesSerializer(serializers.ModelSerializer, TrackingSourcesValidatorMixin):
    tracking_sources = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(TRACKING_SOURCE_CHOICES)),
        required=False,
        allow_empty=False,
    )

    class Meta:
        model = User
        fields = (
            'theme',
            'language',
            'currency',
            'display_currency',
            'tracking_sources',
            'onboarding_completed',
        )


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email_notifications',
            'telegram_notifications',
            'notify_large_expense',
            'notify_budget_exceeded',
            'notify_daily_summary',
        )


class TelegramProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('telegram_user_id', 'telegram_username', 'telegram_notifications')
        read_only_fields = ('telegram_user_id', 'telegram_username')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TOTPLoginChallengeSerializer(serializers.Serializer):
    login_token = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)


class TOTPSetupSerializer(serializers.Serializer):
    qr_code = serializers.CharField()
    secret = serializers.CharField()


class TOTPEnableSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)
    secret = serializers.CharField(max_length=32)


class TOTPDisableSerializer(serializers.Serializer):
    password = serializers.CharField()


class TOTPVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)
