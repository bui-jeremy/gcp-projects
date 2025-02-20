from google.cloud import storage, logging as cloudLogging, pubsub_v1
from flask import abort, request
import json

cloudLoggingClient = cloudLogging.Client()
cloudLogger = cloudLoggingClient.logger("cloud-function-log")
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('ds561-bucs', 'banned-country-topic')

def fetchFileFromBucket(bucketPath):
    if '/' not in bucketPath:
        return None
    bucketName, filePath = bucketPath.split('/', 1)
    bucket = storage.Client().get_bucket(bucketName)
    blob = bucket.blob(filePath)
    if blob.exists():
        return blob.download_as_text()
    return None

def checkBannedCountry():
    country = request.headers.get('X-Country', 'unknown')
    if country in ['North Korea', 'Iran', 'Cuba', 'Myanmar', 'Iraq', 'Libya', 'Sudan', 'Zimbabwe', 'Syria']:
        message = json.dumps({'country': country})
        publisher.publish(topic_path, message.encode('utf-8'))
        return True
    return False

def serve_file(request):
    bucketPath = request.path.lstrip('/')
    if request.method != 'GET':
        cloudLogger.log_text('Unsupported HTTP method: ' + request.method + ' was used for ' + bucketPath, severity='ERROR')
        abort(501, description="Not Implemented")

    if checkBannedCountry():
        abort(400, description="Permission Denied. The request is coming from a banned country.")

    fileContent = fetchFileFromBucket(bucketPath)
    if fileContent is None:
        cloudLogger.log_text('File ' + bucketPath + ' is missing', severity='ERROR')
        abort(404, description="The file has not been found!")
    
    return (fileContent, 200)

def manageErrors(error):
    cloudLogger.log_text('Error occurred: ' + str(error), severity='ERROR')
    return {'error': str(error)}, error.code
