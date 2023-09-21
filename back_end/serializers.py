from rest_framework import serializers
from .models import Item, University, User, UserCSV, UserPDF, Client
from cloudinary.utils import cloudinary_url 
from urllib.parse import urlparse, urlunparse

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


class TextSerializer(serializers.Serializer):
    sample_text = serializers.CharField()
    personalize = serializers.BooleanField(required=False, default=False)  # Add this line


class ChatbotQuerySerializer(serializers.Serializer):
    question = serializers.CharField()


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ('id', 'name')

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    university = UniversitySerializer(read_only=True)  # Add this line
    

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'profile_picture', 'university', 'is_admin')  # Include 'is_superuser'
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return cloudinary_url(str(obj.profile_picture))[0]  # Cloudinary URL
        return None

class GeneratePdfSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, required=True)
    title = serializers.CharField(max_length=255, required=True)
    date = serializers.CharField(max_length=255, required=True)
    university = serializers.ChoiceField(choices=[('1', 'Birmingham'), ('2', 'Warwick')], required=True)
    question = serializers.CharField()

class UserPDFSerializer2(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Assuming you have the User model imported
    pdf_file = serializers.FileField()
    name = serializers.CharField(max_length=255, default='safequeen')
    created_at = serializers.DateTimeField(read_only=True)  # Setting this to read_only because it's auto_now_add
    functional_titles = serializers.ListField(child=serializers.CharField(max_length=200, default='Authentication Pages'), default=list, allow_empty=True)
    functional_requirements = serializers.ListField(child=serializers.ListField(child=serializers.CharField(max_length=500, default='The web app must allow users to register and login using email and password.'), default=list, allow_empty=True), default=list, allow_empty=True)
    non_functional_titles = serializers.ListField(child=serializers.CharField(max_length=200, default='Reliability'), default=list, allow_empty=True)
    non_functional_requirements = serializers.ListField(child=serializers.ListField(child=serializers.CharField(max_length=500, default='The web app must have a minimum uptime of 99.99%.'), default=list, allow_empty=True), default=list, allow_empty=True)

    class Meta:
        model = UserPDF
        fields = ('user', 'pdf_file', 'name', 'created_at', 'functional_titles', 'functional_requirements', 'non_functional_titles', 'non_functional_requirements')

class GeneratePdfSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, required=True)
    title = serializers.CharField(max_length=255, required=True)
    date = serializers.CharField(max_length=255, required=True)
    university = serializers.ChoiceField(choices=[('1', 'Birmingham'), ('2', 'Warwick')], required=True)
    


class VenueFetchSerializer(serializers.Serializer):
    city_name = serializers.CharField(max_length=100)
    api_key = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=100)  # Assuming the token is a simple string
    keyword = serializers.CharField(max_length=100)
    csv_file_name = serializers.CharField(max_length=100)


class UserPDFSerializer2(serializers.ModelSerializer):
    pdf_file = serializers.SerializerMethodField()
    name = serializers.CharField(max_length=255, required=True)
    class Meta:
        model = UserPDF
        fields = ('id', 'pdf_file', 'name', 'functional_titles', 'functional_requirements', 'non_functional_titles', 'non_functional_requirements')

    def get_pdf_file(self, obj):
        parsed_url = urlparse(obj.pdf_file.url)
        secure_url = parsed_url._replace(scheme='https')
        return f"{urlunparse(secure_url)}.pdf"


class UserPDFSerializer(serializers.ModelSerializer):
    pdf_file = serializers.SerializerMethodField()
    name = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = UserPDF
        fields = ('id', 'pdf_file','name')

    
    def get_pdf_file(self, obj):
        parsed_url = urlparse(obj.pdf_file.url)
        secure_url = parsed_url._replace(scheme='https')
        return f"{urlunparse(secure_url)}.pdf"
    

class UserCSVSerializer(serializers.ModelSerializer):
    csv_file = serializers.SerializerMethodField()
    name = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = UserCSV
        fields = ('id', 'csv_file', 'category', 'name', 'created_at')

   

    def get_csv_file(self, obj):
        parsed_url = urlparse(obj.csv_file.url)
        secure_url = parsed_url._replace(scheme='https')
        return f"{urlunparse(secure_url)}.csv"
    

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'