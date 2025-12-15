from pathlib import Path
from google.cloud import vision

p = Path(__file__).parent / 'image.png'

client = vision.ImageAnnotatorClient()

with p.open('rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

response = client.document_text_detection(image=image)

print(response.full_text_annotation.text)
