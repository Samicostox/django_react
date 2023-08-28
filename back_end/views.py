from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from .serializers import TextSerializer
import csv
import re
import spacy
import io

# Load the custom-trained NER model
output_dir = "./my_custom_ner_model"
nlp = spacy.load(output_dir)

class ProcessTextView(APIView):
    def post(self, request):
        serializer = TextSerializer(data=request.data)
        if serializer.is_valid():
            sample_text = serializer.validated_data['sample_text']

            # Your first code snippet for extracting emails and mixed info
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

            # Your second code snippet for NER
            output_dir = "./my_custom_ner_model"
            nlp = spacy.load(output_dir)
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

            # Create CSV in memory
            output = io.StringIO()
            fieldnames = ['Mixed', 'Email', 'Companies', 'PersonNames']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for entry in user_list:
                writer.writerow(entry)

            # Create HTTP response with CSV
            output.seek(0)
            response = HttpResponse(output, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="linkedin_data_processed.csv"'
            return response

        return Response({"msg": "Invalid data"})