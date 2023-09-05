from django.db import models
from django.contrib.auth.models import AbstractUser



class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()


class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255,unique= True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    isemailvalid = models.BooleanField(default = False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []



class University(models.Model):
    name = models.CharField(max_length=255)
    
class UserPDF(models.Model):
    user = models.ForeignKey(User, related_name='pdfs', on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='user_pdfs/')
    name = models.CharField(max_length=255, default = 'safequeen')

    def __str__(self):
        return f"PDF for {self.user.email}"