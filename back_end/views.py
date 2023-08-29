from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from .serializers import TextSerializer
import csv
import re
import spacy
import io
import pandas as pd
import openai

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