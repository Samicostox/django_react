
import os
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfReader, PdfWriter
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from back_end.models import User
from react_backend import settings
from .serializers import ChatbotQuerySerializer, GeneratePdfSerializer, TextSerializer, UserSerializer
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


class ProcessTextView(APIView):
    def post(self, request):
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
            df = pd.DataFrame(user_list)

            # Add a new column for personalized emails
            if personalize:  # Check if the boolean is True
                # Add a new column for personalized emails
                df['Mail'] = df['Mixed'].apply(lambda x: personalize_email(x, email_template))
                fieldnames = ['Mixed', 'Email', 'Companies', 'PersonNames', 'Mail']
            else:
                fieldnames = ['Mixed', 'Email', 'Companies', 'PersonNames']

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for index, row in df.iterrows():
                writer.writerow(row.to_dict())

            # Create HTTP response with CSV
            output.seek(0)
            response = HttpResponse(output, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="linkedin_data_processed.csv"'
            return response

        return Response({"msg": "Invalid data"})
    


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
                user.isemailvalid = True  # Assuming you have this field to keep track of email verification status
                user.email_verification_code = None  # Clear the code
                user.save()
                return Response({"msg": "Successfully verified email"}, status=status.HTTP_200_OK)
            else:
                return Response({"msg": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:  # Replace CustomUser with your actual User model
            return Response({"msg": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    def post(self, request):
        user = authenticate(email=request.data['email'], password=request.data['password'])
        if user:
            if user.isemailvalid:
                token, created = Token.objects.get_or_create(user=user)  # This will get the token if it exists, otherwise it will create one.
                return Response({"msg": "Successfully logged in!", "token": token.key}, status=status.HTTP_200_OK)
            else:
                return Response({"msg": "Please verify your email first"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"msg": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyEmail(APIView):
    def get(self, request, token):
        try:
            token_obj = Token.objects.get(key=token)
            user = token_obj.user   
            if not user.isemailvalid:
                user.isemailvalid = True
                user.save()
            return Response({"msg": "Successfully verified email"}, status=status.HTTP_200_OK)
        except:
            return Response({"msg": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)




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
    model_engine = "ft:gpt-3.5-turbo-0613:personal::7uMHQkkK"  # Replace with your fine-tuned model ID
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
    
    return buffer_requirements

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

            buffer_requirements = generate_requirements_pdf(question)

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

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="final_document.pdf"'
            
            return response
        return Response({"msg": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)