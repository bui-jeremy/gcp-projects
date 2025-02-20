from http.server import BaseHTTPRequestHandler, HTTPServer
from google.cloud import storage, logging as cloudLogging, pubsub_v1
import json
import requests 

# Google Cloud Logging setup
cloudLoggingClient = cloudLogging.Client()
cloudLogger = cloudLoggingClient.logger("httpServerLog")

# Configuration
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
    bucket = storage.Client().get_bucket(bucketName)
    blob = bucket.blob(filePath)
    if blob.exists():
        return blob.download_as_text()
    return None

def get_zone():
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/zone"
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(metadata_url, headers=headers)
    if response.status_code == 200:
        return response.text.split('/')[-1]  
    return "unknown"

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        super().log_message(format, *args)

    def do_GET(self):
        country = self.headers.get('X-Country', 'unknown')
        if country in bannedCountries:
            cloudLogger.log_text("Access denied from banned country: " + country, severity="ERROR")
            notifyTrackerApp(country)
            self.response_code = 400
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Access denied: Request from banned country")
            return

        try:
            fileContent = fetchFileFromBucket(self.path.strip("/"))
            if fileContent is None:
                cloudLogger.log_text("File " + self.path + " not found", severity="ERROR")
                self.response_code = 404
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
            else:
                zone = get_zone()
                self.response_code = 200
                self.send_response(200)
                self.send_header("X-Instance-Zone", zone)  
                self.end_headers()
                self.wfile.write(fileContent.encode("utf-8"))
        except BrokenPipeError:
            cloudLogger.log_text("The server has timed out!", severity="ERROR")
            print("The server has timed out!")
        except Exception as e:
            cloudLogger.log_text("Error occurred: " + str(e), severity="ERROR")
            self.response_code = 500
            self.send_response(500)
            self.end_headers()

    def handle_unsupported_methods(self):
        cloudLogger.log_text("Unsupported method " + self.command + " was used for " + self.path, severity="ERROR")
        self.response_code = 501
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
    print(f"Server running on {serverAddress}:{port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped by user.")
    finally:
        server.server_close()
        print("Server has been cleaned up.")
        
if __name__ == "__main__":
    runServer("0.0.0.0", 8080)
