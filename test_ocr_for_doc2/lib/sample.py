from pathlib import Path
from google.cloud import vision

from declare_key import call_for_client

p = Path(__file__).parent.parent / 'documents/images/sample/sample.png'

#client = vision.ImageAnnotatorClient()  
client = call_for_client() # Use the imported function to get the client, this way the key file path is centralized
with p.open('rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

response = client.document_text_detection(image=image)

print(response.full_text_annotation.text)
