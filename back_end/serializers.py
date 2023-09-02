from rest_framework import serializers
from .models import Item, User

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


class TextSerializer(serializers.Serializer):
    sample_text = serializers.CharField()
    personalize = serializers.BooleanField(required=False, default=False)  # Add this line


class ChatbotQuerySerializer(serializers.Serializer):
    question = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'username')
        extra_kwargs = {'password': {'write_only': True}}