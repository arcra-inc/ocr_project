from google.cloud import vision

# このキーパスを入力した場合，githubに上げてはいけません
def call_for_client():
    client = vision.ImageAnnotatorClient.from_service_account_file(
        "C:\path\to\your\service-account-key.json"
    )
    return client