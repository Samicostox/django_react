from django.db import models
from django.contrib.auth.models import AbstractUser



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
    profile_picture = models.ImageField(
        upload_to='profile_pics/', null=True, blank=True, default="profile_pics/PHOTO-2023-09-04-11-14-23_vEOc0v8.jpg"
    )
    university = models.ForeignKey(University, related_name='students', on_delete=models.SET_NULL, null=True, blank=True
    )  # ForeignKey to University model

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email




    
class UserPDF(models.Model):
    user = models.ForeignKey(User, related_name='pdfs', on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='user_pdfs/')
    name = models.CharField(max_length=255, default = 'safequeen')

    def __str__(self):
        return f"PDF for {self.user.email}"
    
class UserCSV(models.Model):
    CATEGORY_CHOICES = [
        ('Type1', 'Email'),  # First type of CSV file
        ('Type2', 'Phone')   # Second type of CSV file
    ]

    user = models.ForeignKey(User, related_name='csvs', on_delete=models.CASCADE)
    csv_file = models.FileField(upload_to='user_csvs/')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=255, default='safecsv')

    def __str__(self):
        return f"CSV for {self.user.email} of category {self.category}"
