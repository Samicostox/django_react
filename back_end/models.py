from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.contrib.postgres.fields import ArrayField
from django.forms import JSONField

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

class University(models.Model):
    name = models.CharField(max_length=255)


class User(AbstractUser):
    username = None
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_email_valid = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    profile_picture = CloudinaryField('profile_picture', null=True, blank=True, default="https://res.cloudinary.com/dl2adjye7/image/upload/rgpqrf6envo22zzgnndfNone")
    university = models.ForeignKey(University, related_name='students', on_delete=models.SET_NULL, null=True, blank=True
                                   
    ) 
    is_admin = models.BooleanField(default=False)
     # ForeignKey to University model
    # Add this line to your User model
    password_reset_code = models.CharField(max_length=6, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class UserPDF(models.Model):
    user = models.ForeignKey(User, related_name='pdfs', on_delete=models.CASCADE)
    pdf_file = CloudinaryField('pdf_file')
    name = models.CharField(max_length=255, default = 'safequeen')
    created_at = models.DateTimeField(auto_now_add=True)
    functional_titles = ArrayField(models.CharField(max_length=200, default='Authentication Pages'), blank=True, default=list)
    non_functional_titles = ArrayField(models.CharField(max_length=200, default='Reliability'), blank=True, default=list)
    non_functional_requirements = models.JSONField(blank=True, default=list)
    functional_requirements = models.JSONField(blank=True, default=list)
    name_of_project = models.CharField(max_length=255, blank=True, default='')
    type_of_project = models.CharField(max_length=255, blank=True, default='')
    name_of_client_company = models.CharField(max_length=255, blank=True, default='')
    consultant_name = models.CharField(max_length=255, blank=True, default='')
    scope = models.CharField(max_length=10000, blank=True, default='')

    
      

    def __str__(self):
        return f"PDF for {self.user.email}"
    
class UserCSV(models.Model):
    CATEGORY_CHOICES = [
        ('Type1', 'Email'),  # First type of CSV file
        ('Type2', 'Phone')   # Second type of CSV file
    ]

    user = models.ForeignKey(User, related_name='csvs', on_delete=models.CASCADE)
    csv_file = CloudinaryField('csv_file')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=255, default='safecsv')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CSV for {self.user.email} of category {self.category}"


class Client(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    company = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    message = models.TextField()
    budget = models.CharField(max_length=255)  # Budget as a string

    def __str__(self):
        return f"{self.first_name} {self.last_name} from {self.company}"