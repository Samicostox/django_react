from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
import math
import os
import time
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfReader, PdfWriter
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404, HttpResponse
from cloudinary.uploader import upload

from back_end.models import University, User, UserCSV, UserPDF
from react_backend import settings
from .serializers import ChatbotQuerySerializer, GeneratePdfSerializer, GeneratePdfSerializer2, TextSerializer, UniversitySerializer, UserCSVSerializer, UserPDFSerializer, UserSerializer, VenueFetchSerializer
import csv
import re
import spacy
import io
import pandas as pd
import openai
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
import random
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import re
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import concurrent.futures
# Load the custom-trained NER model
output_dir = "./my_custom_ner_model"
nlp = spacy.load(output_dir)

openai.api_key = "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"



# Specify the model
model = 'text-davinci-003'

email_template = """
Hi [name],

I hope this email finds you well!

I was looking at the University of Birmingham's alumni and came across [company]. [personalised paragraph about the company or sector]

I recently graduated from the University of Birmingham, and last year some fellow students and myself created Birmingham Innovation Studio. A student run company, we offer tech and business services all carried out by students. This is a great way for students to apply what they have learned at university while getting a first work experience but also allows us to have a very competitive price. We could also place students in your company if you are not interested in outsourcing.

I would love to get on call with you guys to see if there is any way we could help you out with our services! Let me know if you would be free this week to discuss this potential collaboration.

Please find attached our Pitchbook to learn more about us!

Best,
Sami Ribardiere
"""
import cloudinary.uploader
# Function to personalize email
def personalize_email(mixed_info, email_template):
    prompt = f"Based on these informations : {mixed_info}, please fill the [] in following email: {email_template}"
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=500
    )
    personalized_email = response.choices[0].text.strip()
    print(f"Personalized email for {mixed_info}:\n{personalized_email}\n")
    return personalized_email

def ask_gpt4(question):
    model_engine = "gpt-4"  # Replace with the actual GPT-4 engine ID when it becomes available
    messages = [
        {"role": "system", "content": "You are a code generator specialised in ORDA programming language by 4D. You only generate code"},
        {"role": "user", "content": question}
    ]
    
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=messages
    )
    
    answer = response['choices'][0]['message']['content']
    return answer

@shared_task
def generate_csv_and_save(user_id, user_list, personalize, email_template):
    # Your logic here
    df = pd.DataFrame(user_list)

    if personalize:
        df['Mail'] = df['Mixed'].apply(lambda x: personalize_email(x, email_template))
        fieldnames = ['Mixed', 'Email', 'Companies', 'PersonNames', 'Mail']
    else:
        fieldnames = ['Mixed', 'Email', 'Companies', 'PersonNames']

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index, row in df.iterrows():
        writer.writerow(row.to_dict())

    output.seek(0)
    csv_file_name = "generated_leads"

    absolute_path = os.path.abspath(f"{csv_file_name}.csv")
    print(f"Saving file to {absolute_path}")
    csv_content = output.getvalue().encode('utf-8')
    uploaded = cloudinary.uploader.upload(
        csv_content,
        resource_type="raw",
        public_id=f"{csv_file_name}.csv",
        format="csv"
    )

    user_csv = UserCSV(
                    user_id=user_id,
                    name=csv_file_name,
                    category='email' , # Setting the category to "email"
                    csv_file=uploaded['url']
                )
            
            
    user_csv.save()

    

class ProcessTextView(APIView):
    def post(self, request):
        token = request.data.get('token', None)
        
        if token is None:
            raise AuthenticationFailed('No token provided')
            
        # Validate the token
        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
        
        serializer = TextSerializer(data=request.data)
        if serializer.is_valid():
            sample_text = serializer.validated_data['sample_text']
            personalize = serializer.validated_data.get('personalize', False)

            # Extracting emails and mixed info
            raw_blocks = sample_text.strip().split("\n\n")
            formatted_blocks = []
            for i in range(0, len(raw_blocks), 2):
                try:
                    formatted_blocks.append(f"{raw_blocks[i]}\n\n{raw_blocks[i+1]}")
                except IndexError:
                    formatted_blocks.append(raw_blocks[i])
            email_list = []
            mixed_list = []
            formatted_blocks = [block for block in formatted_blocks if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', block)]
            for block in formatted_blocks:
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', block)
                if email_match:
                    email = email_match.group(0)
                    email_list.append(email)
                lines = block.strip().split('\n')
                mixed_list.append(lines[0].strip())
            user_list = []
            for i in range(min(len(email_list), len(mixed_list))):
                user_list.append({"Mixed": mixed_list[i], "Email": email_list[i]})

            # NER
            for entry in user_list:
                mixed = entry.get('Mixed', '')
                doc = nlp(mixed)
                person_names = []
                companies = []
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        person_names.append(ent.text)
                    elif ent.label_ == 'ORG':
                        companies.append(ent.text)
                entry['PersonNames'] = ", ".join(person_names)
                entry['Companies'] = ", ".join(companies)

            # Create a DataFrame from the user_list
            generate_csv_and_save.apply_async(
                args=[request.user.id, user_list, personalize, email_template],
                countdown=1  # Run task one second from now
            )

            return Response({"msg": "Your request is being processed. You'll be notified once the CSV is ready."})

        return Response({"msg": "Invalid data"})






class AddUniversityView(APIView):
    def post(self, request):
        serializer = UniversitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Successfully added university!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AskChatbotView(APIView):
    def post(self, request):
        # Manually get token from the JSON body
        token = request.data.get('token', None)
        
        if token is None:
            raise AuthenticationFailed('No token provided')
            
        # Validate the token
        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
            
        # Your existing code
        serializer = ChatbotQuerySerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            answer = ask_gpt4(question)  # Assuming `ask_gpt4` is defined elsewhere
            return Response({"answer": answer})
        
        return Response({"msg": "Invalid data"})

    
# Generate a random 6-digit verification code


class SignUpView(APIView):
   def post(self, request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        
        # Generate a 6-digit code
        verification_code = str(random.randint(100000, 999999))
        user.email_verification_code = verification_code

        # Handle profile picture (if provided)
        image_file = request.FILES.get('profile_picture', None)
        if image_file:
            uploaded = upload(image_file, resource_type="image")
            user.profile_picture = uploaded['public_id']

        # Handle university (if provided)
        university_id = request.data.get('university', None)  # Replace 'university' with the field name in your frontend form
        if university_id:
            try:
                university = University.objects.get(id=university_id)
                user.university = university
            except University.DoesNotExist:
                return Response({"error": "University does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        user.save()

        # Send email
        mail_subject = 'Activate your account.'
        message = f'Your verification code is: {verification_code}'
        send_mail(mail_subject, message, 'from_email', [user.email])

        return Response({"msg": "Successfully signed up! Please check your email for the verification code"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailCode(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        try:
            user = User.objects.get(email=email)  # Replace CustomUser with your actual User model
            if user.email_verification_code == code:
                user.is_email_valid = True  # Assuming you have this field to keep track of email verification status
                user.email_verification_code = None  # Clear the code
                user.save()
                return Response({"msg": "Successfully verified email"}, status=status.HTTP_200_OK)
            else:
                return Response({"msg": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:  # Replace CustomUser with your actual User model
            return Response({"msg": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)

from cloudinary.utils import cloudinary_url

class LoginView(APIView):
    def post(self, request):
        user = authenticate(email=request.data['email'], password=request.data['password'])
        if user:
            if user.is_email_valid:
                token, created = Token.objects.get_or_create(user=user)  # This will get the token if it exists, otherwise it will create one.
                image_url = None
                if user.profile_picture:
                    image_url = cloudinary_url(str(user.profile_picture),secure=True)[0]

                return Response({"msg": "Successfully logged in!", "token": token.key, "university": user.university.name, "name" : user.name, "profile_picture" : image_url}, status=status.HTTP_200_OK)
            else:
                return Response({"msg": "Please verify your email first"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"msg": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyEmail(APIView):
    def get(self, request, token):
        try:
            token_obj = Token.objects.get(key=token)
            user = token_obj.user   
            if not user.is_email_valid:
                user.is_email_valid = True
                user.save()
            return Response({"msg": "Successfully verified email"}, status=status.HTTP_200_OK)
        except:
            return Response({"msg": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class RetrieveUserInfo(APIView):
    
    def post(self, request, *args, **kwargs):
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')
        
        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
        
        user = request.user
        user_serializer = UserSerializer(user)
        
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class UpdateUserInfo(APIView):
    
    def put(self, request, *args, **kwargs):
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')
        
        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        try:
            user = request.user

            # You can now use serializers or manually save the fields.
            user.name = request.data.get('name', user.name)
            user.profile_picture = request.data.get('profile_picture', user.profile_picture)
            user.university_id = request.data.get('university', user.university_id)
            
            # Save the updated user model
            user.save()

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Activate the user
        user.is_active = True
        user.save()
        # Maybe log the user in
        # Do additional things like sending a welcome email
        return redirect('some_view')  # Replace with a view name you'd like to redirect to
    else:
        return render(request, 'activation_failed.html')  # Replace with your failed activation template
    

def ask_gpt_custom(question):
    model_engine = "ft:gpt-3.5-turbo-0613:personal::7wtZ7Z9e"  # Replace with your fine-tuned model ID
    messages = [
        {"role": "system", "content": "You are a tech specialist and you create functional and non-functional requirements."},
        {"role": "user", "content": "write me the functional and non functional requirements of the following app" + question}
    ]
    
   

    # Making API call using the chat completions endpoint
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=messages,
        max_tokens=2000
    )

    answer = response['choices'][0]['message']['content']
    return answer


def generate_pdf(buffer, answer):
    styles = getSampleStyleSheet()
    bullet_style = ParagraphStyle('Bullet', parent=styles['BodyText'], firstLineIndent=0, leftIndent=36, spaceAfter=0, bulletIndent=0)
    subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading1'], fontSize=14)
    main_heading_style = ParagraphStyle('MainHeading', parent=styles['Heading1'], fontSize=18)
    
    # Create a new style for the biggest title
    biggest_heading_style = ParagraphStyle('BiggestHeading', parent=styles['Heading1'], fontSize=24)

    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    # Parse and format the content
    story = []
    for line in answer.split('\n'):
        if line == "2 Requirements":
            # Use the biggest_heading_style for this specific line
            story.append(Paragraph(line, biggest_heading_style))
        elif line.startswith("1.1") or line.startswith("2.1") or line.startswith("1.2") or line.startswith("2.2"):
            story.append(Paragraph(line, main_heading_style))
        elif line.endswith(":"):
            story.append(Paragraph(line, styles['Heading2']))
        elif line.startswith("•"):
            story.append(Paragraph(line, bullet_style))
        else:
            story.append(Paragraph(line, styles['BodyText']))
        story.append(Spacer(1, 12))

    pdf.build(story)


def generate_first_page_pdf(user_title, user_date, user_university):
    buffer_first_page = io.BytesIO()
    
    pdf = SimpleDocTemplate(
        buffer_first_page,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    pdfmetrics.registerFont(TTFont('SomeFont', './back_end/fonts/cmu.bright-roman.ttf'))
    pdfmetrics.registerFont(TTFont('SomeFont2', './back_end/fonts/cmu.sans-serif-medium.ttf'))

    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=24, spaceAfter=20, fontName='SomeFont2'))
    styles.add(ParagraphStyle(name='NormalCenter', alignment=1, fontSize=16, spaceAfter=10, fontName='SomeFont'))

    title = Paragraph(user_title, styles['Center'])
    spacer_small = Spacer(1, 0.2*inch)
    technical_document_text = Paragraph("Technical Document", styles['NormalCenter'])
    image_path = "./back_end/Icon-maskable-192 (2).png" if user_university == '1' else "./back_end/elephant.png"
    image = Image(image_path, width=6*inch, height=6*inch)
    project_presented_by_text = Paragraph(
        "A project presented by Birmingham Innovation Studio" if user_university == '1' else "A project presented by Warwick Innovation Studio",
        styles['NormalCenter']
    )
    date_text = Paragraph(f"Date: {user_date}", styles['NormalCenter'])
    elements = [title, spacer_small, technical_document_text, spacer_small, image, spacer_small, project_presented_by_text, spacer_small, date_text]
    pdf.build(elements)
    
    return buffer_first_page

def generate_requirements_pdf(question):
    buffer_requirements = io.BytesIO()
    answer = ask_gpt_custom(question)
    # Assuming generate_pdf is a function you've defined elsewhere
    generate_pdf(buffer_requirements, answer)
    print(answer)
    
    return buffer_requirements, answer

def generate_intro_pdf(data,user_university,question):
    buffer_intro = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer_intro,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # Style Definitions
    pdfmetrics.registerFont(TTFont('SomeFont', './back_end/fonts/cmu.bright-roman.ttf'))
    pdfmetrics.registerFont(TTFont('SomeFont2', './back_end/fonts/cmu.sans-serif-medium.ttf'))
    pdfmetrics.registerFont(TTFont('SomeFont3', './back_end/fonts/cmu.sans-serif-bold.ttf'))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BigHeading', alignment=0, fontSize=24, spaceAfter=40, fontName='SomeFont3'))
    styles.add(ParagraphStyle(name='SubHeading', alignment=0, fontSize=18, spaceAfter=30, fontName='SomeFont3'))
    styles['BodyText'].spaceAfter = 12
    styles['BodyText'].leading = 18  # 1.5-line spacing

    # Elements
    title = Paragraph("1. Introduction", styles['BigHeading'])
    sub_heading1 = Paragraph("1.1 Purpose of this document", styles['SubHeading'])
    sub_heading2 = Paragraph("1.2 Scope", styles['SubHeading'])
    sub_heading3 = Paragraph("1.3 References", styles['SubHeading'])
    
    intro_paragraph_text = ("This document explains the functional specification of {}, "
                            "the {} project in which {}, engages to fulfill all the requests "
                            "demanded by {} as explained during elementary meetings and calls."
                            ).format(data['name_of_project'], data['type_of_project'], 
                                     "Warwick Innovation Studio" if user_university == '2' else "Birmingham Innovation Studio", 
                                     data['name_of_client_company'])

    intro_paragraph = Paragraph(intro_paragraph_text, styles['BodyText'])

    para1_text = ("The functional specification document serves the same purpose as a contract. "
                  "The specifications presented in this document are related to the conversations done by {}. "
                  "Following this document, the developers agree to provide the capabilities specified "
                  "and fulfill all requests and demands of {}, who also agreed to find the product "
                  "satisfactory if it provides the capabilities as specified."
                  ).format(data['consultant_name'], data['name_of_client_company'])

    para1 = Paragraph(para1_text, styles['BodyText'])
    
    para2_text = question
    para2 = Paragraph(para2_text, styles['BodyText'])

    para3_text = "All meetings, emails and materials exchanges with {}.".format(data['name_of_client_company'])
    para3 = Paragraph(para3_text, styles['BodyText'])

    spacer_small = Spacer(1, 0.2 * inch)
    spacer_large = Spacer(1, 0.5 * inch)  # Larger spacer for more space between sections

    # Combine all elements with spacers
    elements = [title, intro_paragraph, spacer_large, sub_heading1, para1, spacer_large, sub_heading2, para2, spacer_large, sub_heading3, para3]
    
    pdf.build(elements)
    
    return buffer_intro

def process_requirements(answer):
    # Initialize lists
    functional_titles = []
    functional_requirements = []
    non_functional_titles = []
    non_functional_requirements = []

    # Split the text into functional and non-functional parts
    functional_text, non_functional_text = answer.split("2.2 Non-Functional Requirements")

    # Further split each part into sections based on digit and period (e.g., "1. ", "2. ", etc.)
    functional_sections = re.split(r'\d+\. ', functional_text)[1:]  # Skip the first empty string
    non_functional_sections = re.split(r'\d+\. ', non_functional_text)[1:]  # Skip the first empty string

    # Process functional sections
    for section in functional_sections:
        lines = section.strip().split('\n')
        title = lines[0].strip().replace(':', '')
        requirements = [line.replace('• ', '').strip() for line in lines[1:]]
        functional_titles.append(title)
        functional_requirements.append(requirements)

    # Process non-functional sections
    for section in non_functional_sections:
        lines = section.strip().split('\n')
        title = lines[0].strip().replace(':', '')
        requirements = [line.replace('• ', '').strip() for line in lines[1:]]
        non_functional_titles.append(title)
        non_functional_requirements.append(requirements)

    return functional_titles, functional_requirements, non_functional_titles, non_functional_requirements


class GenerateRequirementsPDF(APIView):
    def post(self, request):
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        serializer = GeneratePdfSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            user_title = serializer.validated_data.get('title')
            user_date = serializer.validated_data.get('date')
            user_university = serializer.validated_data.get('university')

            buffer_first_page = generate_first_page_pdf(user_title, user_date, user_university)

            intro_data = {
                'name_of_project': request.data.get('name_of_project'),
                'type_of_project': request.data.get('type_of_project'),
                'name_of_client_company': request.data.get('name_of_client_company'),
                'consultant_name': request.data.get('consultant_name'),
                
            }
            buffer_intro = generate_intro_pdf(intro_data,user_university,question)

            buffer_requirements, answer = generate_requirements_pdf(question)  # Get answer here
            functional_titles, functional_requirements, non_functional_titles, non_functional_requirements = process_requirements(answer)
            

            # Combine PDFs
            buffer_first_page.seek(0)
            buffer_intro.seek(0)
            buffer_requirements.seek(0)
            
            pdf_reader1 = PdfReader(buffer_first_page)
            pdf_reader2 = PdfReader(buffer_intro)
            pdf_reader3 = PdfReader(buffer_requirements)
            
            pdf_writer = PdfWriter()

            for i in range(len(pdf_reader1.pages)):
                pdf_writer.add_page(pdf_reader1.pages[i])
            for i in range(len(pdf_reader2.pages)):
                pdf_writer.add_page(pdf_reader2.pages[i])
            for i in range(len(pdf_reader3.pages)):
                pdf_writer.add_page(pdf_reader3.pages[i])

            final_pdf_buffer = io.BytesIO()
            pdf_writer.write(final_pdf_buffer)
            pdf_content = final_pdf_buffer.getvalue()
            final_pdf_buffer.close()

            pdf_name = f"final_document_{request.user.id}.pdf"
            pdf_file = ContentFile(pdf_content, name=pdf_name)
            user_pdf = UserPDF.objects.create(user=request.user, pdf_file=pdf_file, name = intro_data['name_of_project'])

            ##response = HttpResponse(pdf_content, content_type='application/pdf')
            ##response['Content-Disposition'] = 'attachment; filename="final_document.pdf"'
            
            return Response({
                "functional_titles": functional_titles,
                "functional_requirements": functional_requirements,
                "non_functional_titles": non_functional_titles,
                "non_functional_requirements": non_functional_requirements
            })

        return Response({"msg": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
    
class RetrieveUserPDFs(APIView):
    def get_object(self, user):
        try:
            return UserPDF.objects.filter(user=user)
        except UserPDF.DoesNotExist:
            raise Http404

    def post(self, request):
        # Explicitly check for a token in the request data
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        # Continue with existing logic
        user_pdfs = self.get_object(request.user)
        serializer = UserPDFSerializer(user_pdfs, many=True)
        return Response(serializer.data)
    
def fetch_venues(api_key, location, radius, keyword):
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    venues = []
    params = {
        "location": location,
        "radius": radius,
        "keyword": keyword,
        "key": api_key
    }

    while True:
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            results = response.json()
            venues.extend(results.get('results', []))

            next_page_token = results.get('next_page_token')
            if next_page_token:
                params['pagetoken'] = next_page_token
                time.sleep(5)
            else:
                break
        else:
            break

    return venues



def fetch_place_details(api_key, place_id):
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,international_phone_number,website,opening_hours,types",
        "key": api_key
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_offsets(city_latitude, distance_km=3):
    # Convert latitude from degrees to radians
    lat_rad = math.radians(city_latitude)

    # Calculate the offsets in degrees
    offset_in_degrees_lat = distance_km / 111
    offset_in_degrees_lng = distance_km / (111 * math.cos(lat_rad))

    # Define number of rows and columns for the grid
    rows = 4
    columns = 5

    # Half of rows and columns to center the grid
    half_rows = rows // 2
    half_columns = columns // 2

    # Create a grid of offsets
    offsets_lat = [i * offset_in_degrees_lat for i in range(-half_rows, half_rows + 1)]
    offsets_lng = [i * offset_in_degrees_lng for i in range(-half_columns, half_columns + 1)]

    return offsets_lat, offsets_lng


def get_city_coordinates(api_key, city_name):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    params = {
        "address": city_name,
        "key": api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        results = response.json()
        # Check if results list is not empty
        if results['results']:
            location = results['results'][0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            return lat, lng
        else:
            print("No results found for the given city name.")
            return None, None
    else:
        print("Error fetching data from API")
        return None, None
    


# Assuming the other functions you've mentioned are imported here as well


@shared_task
def fetch_and_create_csv(api_key, city_name, keyword, csv_file_name, token):
    try:
        # Simulate the authentication inside the task
        auth_token = Token.objects.get(key=token)
        user = auth_token.user
    except Token.DoesNotExist:
        return "Invalid token"

    try:
        # Your existing code adapted for the task
        lat, lng = get_city_coordinates(api_key, city_name)
        if lat is None and lng is None:
            return "Invalid API key"

        offsets_lat, offsets_lng = get_offsets(lat, 3)

        locations = [(lat + offset_lat, lng + offset_lng)
                    for offset_lat in offsets_lat
                    for offset_lng in offsets_lng][:20]
        locations = [f"{lat},{lng}" for lat, lng in locations]

        radius = "2000"

        all_venues = []
        # Assuming you've imported concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_location = {executor.submit(fetch_venues, api_key, location, radius, keyword): location for location in locations}
            for future in concurrent.futures.as_completed(future_to_location):
                all_venues.extend(future.result())

        venues = []
        for result in all_venues:
            name = result.get('name')
            address = result.get('vicinity')
            place_id = result.get('place_id')
            details = fetch_place_details(api_key, place_id)

            if details:
                phone_number = details['result'].get('formatted_phone_number', 'Not Available')
                website = details['result'].get('website', 'Not Available')
                types_list = details['result'].get('types', ['Not Available'])
                main_type = types_list[0] if types_list else 'Not Available'
                opening_hours = details['result'].get('opening_hours', {}).get('weekday_text', ['Not Available']*7)

                venues.append({
                            'name': name,
                            'address': address,
                            'phone_number': phone_number,
                            'website': website,
                            'type': main_type,
                            'Monday': opening_hours[0],
                            'Tuesday': opening_hours[1],
                            'Wednesday': opening_hours[2],
                            'Thursday': opening_hours[3],
                            'Friday': opening_hours[4],
                            'Saturday': opening_hours[5],
                            'Sunday': opening_hours[6]
                        })
            else:
                        venues.append({
                            'name': name,
                            'address': address,
                            'phone_number': 'Not Available',
                            'website': 'Not Available',
                            'type': 'Not Available',
                            'Monday': 'Not Available',
                            'Tuesday': 'Not Available',
                            'Wednesday': 'Not Available',
                            'Thursday': 'Not Available',
                            'Friday': 'Not Available',
                            'Saturday': 'Not Available',
                            'Sunday': 'Not Available'
                        })

        df = pd.DataFrame(venues)
        df = df.drop_duplicates()

        output = io.StringIO()
        fieldnames = list(df.columns)
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in df.iterrows():
            writer.writerow(row.to_dict())

        output.seek(0)
        csv_content = output.getvalue().encode('utf-8')

        uploaded = cloudinary.uploader.upload(
            csv_content,
            resource_type="raw",
            public_id=f"{csv_file_name}.csv",
            format="csv"
        )

        user_csv = UserCSV(
            user=user,
            name=csv_file_name,
            category='phone',
            csv_file=uploaded['url']
        )

        user_csv.save()

        return "CSV created successfully"

    except Exception as e:
        return str(e)



class FetchVenuesView(APIView):
    def post(self, request):
        print("Received POST request")
        token = request.data['token']

        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        print(request.data)
        serializer = VenueFetchSerializer(data=request.data)

        if serializer.is_valid():
            city_name = serializer.validated_data['city_name']
            api_key = serializer.validated_data['api_key']
           
            keyword = serializer.validated_data['keyword']
            csv_file_name = serializer.validated_data['csv_file_name']

        fetch_and_create_csv.apply_async(args=[api_key, city_name, keyword, csv_file_name, token])
        return Response({"msg": "Your request is being processed. You'll be notified once the CSV is ready."})


class FetchUserPhoneCSVsView(APIView):
    def post(self, request):
        print("Received POST request")
        
        # Token-based authentication
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        # Fetch all CSV files of category 'phone' for the authenticated user
        try:
            user_csvs = UserCSV.objects.filter(user=request.user, category='phone')
        except UserCSV.DoesNotExist:
            return Response({"msg": "No CSV files found"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the queryset
        serializer = UserCSVSerializer(user_csvs, many=True)
        
        return Response({"csv_files": serializer.data}, status=status.HTTP_200_OK)

class FetchUserEmailCSVsView(APIView):
    def post(self, request):
        print("Received POST request")
        
        # Token-based authentication
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        # Fetch all CSV files of category 'phone' for the authenticated user
        try:
            user_csvs = UserCSV.objects.filter(user=request.user, category='email')
        except UserCSV.DoesNotExist:
            return Response({"msg": "No CSV files found"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the queryset
        serializer = UserCSVSerializer(user_csvs, many=True)
        
        return Response({"csv_files": serializer.data}, status=status.HTTP_200_OK)


class FetchUserCSVsView(APIView):
    def post(self, request):
        print("Received POST request")
        
        # Token-based authentication
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        # Fetch all CSV files of category 'phone' for the authenticated user
        try:
            user_csvs = UserCSV.objects.filter(user=request.user)
        except UserCSV.DoesNotExist:
            return Response({"msg": "No CSV files found"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the queryset
        serializer = UserCSVSerializer(user_csvs, many=True)
        
        return Response({"csv_files": serializer.data}, status=status.HTTP_200_OK)
    


def generate_requirements_pdf_from_lists(functional_titles, functional_requirements, non_functional_titles, non_functional_requirements):
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    # Define custom styles
    bullet_style = ParagraphStyle('Bullet', parent=styles['BodyText'], firstLineIndent=0, leftIndent=36, spaceAfter=0, bulletIndent=0)
    subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading1'], fontSize=14)
    main_heading_style = ParagraphStyle('MainHeading', parent=styles['Heading1'], fontSize=18)
    biggest_heading_style = ParagraphStyle('BiggestHeading', parent=styles['Heading1'], fontSize=24)

    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    # Create the story list to hold the PDF elements
    story = []
    
    # Add the main heading for Requirements
    story.append(Paragraph("2 Requirements", biggest_heading_style))
    story.append(Spacer(1, 24))  # Additional space after the main heading

    # Add Functional Requirements
    story.append(Paragraph("2.1 Functional Requirements", main_heading_style))
    story.append(Spacer(1, 18))  # Additional space after the subheading
    
    for title, requirements in zip(functional_titles, functional_requirements):
        story.append(Paragraph(title + ":", styles['Heading2']))
        story.append(Spacer(1, 12))  # Additional space before the content
        for req in requirements:
            story.append(Paragraph("• " + req, bullet_style))
        story.append(Spacer(1, 12))

    # Add Non-Functional Requirements
    story.append(Spacer(1, 40))
    story.append(Paragraph("2.2 Non-Functional Requirements", main_heading_style))
    story.append(Spacer(1, 18))  # Additional space after the subheading
    
    for title, requirements in zip(non_functional_titles, non_functional_requirements):
        story.append(Paragraph(title + ":", styles['Heading2']))
        story.append(Spacer(1, 12))  # Additional space before the content
        for req in requirements:
            story.append(Paragraph("• " + req, bullet_style))
        story.append(Spacer(1, 12))

    # Build the PDF
    pdf.build(story)
    
    # Move the buffer position to the beginning
    buffer.seek(0)
    
    return buffer
# ... (Your existing functions like generate_pdf, generate_first_page_pdf, etc.)

class GenerateCustomRequirementsPDF(APIView):
    def post(self, request):
        token = request.data.get('token', None)
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        serializer = GeneratePdfSerializer2(data=request.data)
        if serializer.is_valid():
            # Extracting data from the request
            functional_titles = request.data.get('functional_titles', [])
            functional_requirements = request.data.get('functional_requirements', [])
            non_functional_titles = request.data.get('non_functional_titles', [])
            non_functional_requirements = request.data.get('non_functional_requirements', [])
            
            intro_data = {
                'name_of_project': request.data.get('name_of_project'),
                'type_of_project': request.data.get('type_of_project'),
                'name_of_client_company': request.data.get('name_of_client_company'),
                'consultant_name': request.data.get('consultant_name'),
            }
            
            user_title = serializer.validated_data.get('title')
            user_date = serializer.validated_data.get('date')
            user_university = serializer.validated_data.get('university')

            buffer_first_page = generate_first_page_pdf(user_title, user_date, user_university)
            buffer_intro = generate_intro_pdf(intro_data, user_university, "Custom Question")  # Replace "Custom Question" as needed
            
            # Assuming you have a function to generate requirements PDF based on the lists
            buffer_requirements = generate_requirements_pdf_from_lists(
                functional_titles, functional_requirements,
                non_functional_titles, non_functional_requirements
            )

            # Combine PDFs
            buffer_first_page.seek(0)
            buffer_intro.seek(0)
            buffer_requirements.seek(0)
            
            pdf_reader1 = PdfReader(buffer_first_page)
            pdf_reader2 = PdfReader(buffer_intro)
            pdf_reader3 = PdfReader(buffer_requirements)
            
            pdf_writer = PdfWriter()

            for i in range(len(pdf_reader1.pages)):
                pdf_writer.add_page(pdf_reader1.pages[i])
            for i in range(len(pdf_reader2.pages)):
                pdf_writer.add_page(pdf_reader2.pages[i])
            for i in range(len(pdf_reader3.pages)):
                pdf_writer.add_page(pdf_reader3.pages[i])

            final_pdf_buffer = io.BytesIO()
            pdf_writer.write(final_pdf_buffer)
            pdf_content = final_pdf_buffer.getvalue()
            final_pdf_buffer.close()

            pdf_name = f"final_document_{request.user.id}.pdf"
            pdf_file = ContentFile(pdf_content, name=pdf_name)
            user_pdf = UserPDF.objects.create(user=request.user, pdf_file=pdf_file, name=intro_data['name_of_project'])

            return Response({"msg": "PDF generated successfully"})

        return Response({"msg": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)



class DeleteUserCSVView(APIView):
    def post(self, request):
        print("Received POST request for deletion")
        
        # Token-based authentication
        token = request.data.get('token', None)
        csv_id = request.data.get('csv_id')
        if token is None:
            raise AuthenticationFailed('No token provided')

        try:
            auth_token = Token.objects.get(key=token)
            request.user = auth_token.user
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        # Fetch the CSV file by ID for the authenticated user
        try:
            user_csv = UserCSV.objects.get(id=csv_id, user=request.user)
        except UserCSV.DoesNotExist:
            raise Http404("CSV file not found")

        # Delete the CSV file
        user_csv.delete()
        
        return Response({"msg": "CSV file deleted successfully"}, status=status.HTTP_200_OK)
