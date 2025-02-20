from http.server import BaseHTTPRequestHandler, HTTPServer
from google.cloud import storage, logging as cloudLogging, pubsub_v1
import json
import socket

cloudLoggingClient = cloudLogging.Client()
cloudLogger = cloudLoggingClient.logger("httpServerLog")
bannedCountries = ['North Korea', 'Iran', 'Cuba', 'Myanmar', 'Iraq', 'Libya', 'Sudan', 'Zimbabwe', 'Syria']

projectId = 'ds561-bucs'
topicId = 'banned-country-topic'

def notifyTrackerApp(country):
    publisher = pubsub_v1.PublisherClient()
    topicPath = publisher.topic_path(projectId, topicId)
    messageData = json.dumps({'country': country}).encode('utf-8')
    publisher.publish(topicPath, messageData)

def fetchFileFromBucket(bucketPath):
    bucketName, filePath = bucketPath.split("/", 1)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(filePath)
    if blob.exists():
        return blob.download_as_text()
    return None

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        super().log_message(format, *args)

    def do_GET(self):
        country = self.headers.get('X-Country', 'unknown')
        if country in bannedCountries:
            cloudLogger.log_text("Access denied from banned country: " + country, severity="ERROR")
            notifyTrackerApp(country)
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Access denied: Request from banned country")
            return

        try:
            fileContent = fetchFileFromBucket(self.path.strip("/"))
            if fileContent is None:
                cloudLogger.log_text("File " + self.path + " not found", severity="ERROR")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(fileContent.encode("utf-8"))
        except BrokenPipeError:
            cloudLogger.log_text("The server has timed out!", severity="ERROR")
            print("The server has timed out!")
        except Exception as e:
            cloudLogger.log_text("Error occurred: " + str(e), severity="ERROR")
            self.send_response(500)
            self.end_headers()

    def handle_unsupported_methods(self):
        cloudLogger.log_text("Unsupported method " + self.command + " was used for " + self.path, severity="ERROR")
        self.send_response(501)
        self.end_headers()
        self.wfile.write((self.command + " not implemented").encode("utf-8"))

    def do_POST(self):
        self.handle_unsupported_methods()

    def do_PUT(self):
        self.handle_unsupported_methods()

    def do_DELETE(self):
        self.handle_unsupported_methods()

    def do_HEAD(self):
        self.handle_unsupported_methods()

    def do_CONNECT(self):
        self.handle_unsupported_methods()

    def do_OPTIONS(self):
        self.handle_unsupported_methods()

    def do_TRACE(self):
        self.handle_unsupported_methods()

    def do_PATCH(self):
        self.handle_unsupported_methods()

def runServer(serverAddress, port):
    server = HTTPServer((serverAddress, port), RequestHandler)
    print(f"Starting server on {serverAddress}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    runServer("0.0.0.0", 8080)
