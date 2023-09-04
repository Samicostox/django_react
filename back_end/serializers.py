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

class GeneratePdfSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, required=True)
    title = serializers.CharField(max_length=255, required=True)
    date = serializers.CharField(max_length=255, required=True)
    university = serializers.ChoiceField(choices=[('1', 'Birmingham'), ('2', 'Warwick')], required=True)
    question = serializers.CharField()


class VenueFetchSerializer(serializers.Serializer):
    city_name = serializers.CharField(max_length=100)
    api_key = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=100)  # Assuming the token is a simple string
    keyword = serializers.CharField(max_length=100)
    csv_file_name = serializers.CharField(max_length=100)