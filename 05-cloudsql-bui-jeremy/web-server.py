from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from google.cloud import storage, logging as cloudLogging, pubsub_v1
import json
import mysql.connector

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
    bucket = storage.Client().get_bucket(bucketName)
    blob = bucket.blob(filePath)
    if blob.exists():
        return blob.download_as_text()
    return None

def log_request_to_db(country, client_ip, gender, age, income, is_banned, time_of_day, requested_file):
    conn = mysql.connector.connect(host="34.42.100.68", user="root", password="", database="hw5")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                   (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file))
    conn.commit()
    cursor.close()
    conn.close()

def log_error_to_db(requested_file, error_code):
    conn = mysql.connector.connect(host="34.42.100.68", user="root", password="", database="hw5")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO failed_requests (req_file, err_code) VALUES (%s, %s)",
                   (requested_file, error_code))
    conn.commit()
    cursor.close()
    conn.close()

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        country = self.headers.get('X-Country', 'unknown')
        client_ip = self.headers.get('X-client-IP', 'unknown')
        gender = self.headers.get('X-gender', 'unknown')
        age = self.headers.get('X-age', 'unknown')
        income = self.headers.get('X-income', 'unknown')
        time_of_day = self.headers.get('X-time', 'unknown')

        is_banned = country in bannedCountries
        if is_banned:
            cloudLogger.log_text("Access denied from banned country: " + country, severity="ERROR")
            notifyTrackerApp(country)
            self.response_code = 400
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Access denied: Request from banned country")
            log_request_to_db(country, client_ip, gender, age, income, True, time_of_day, self.path)
            log_error_to_db(self.path, 400)
            return

        try:
            fileContent = fetchFileFromBucket(self.path.strip("/"))
            if fileContent is None:
                cloudLogger.log_text("File " + self.path + " not found", severity="ERROR")
                self.response_code = 404
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
                log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
                log_error_to_db(self.path, 404)
            else:
                self.response_code = 200
                self.send_response(200)
                self.end_headers()
                self.wfile.write(fileContent.encode("utf-8"))
                log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
        except Exception as e:
            cloudLogger.log_text("Error occurred: " + str(e), severity="ERROR")
            self.response_code = 500
            self.send_response(500)
            self.end_headers()
            log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
            log_error_to_db(self.path, 500)

    def handle_unsupported_methods(self):
        cloudLogger.log_text("Unsupported method " + self.command + " was used for " + self.path, severity="ERROR")
        self.response_code = 501
        self.send_response(501)
        self.end_headers()
        self.wfile.write((self.command + " not implemented").encode("utf-8"))
        log_request_to_db("unknown", "unknown", "unknown", "unknown", "unknown", False, "unknown", self.path)
        log_error_to_db(self.path, 501)

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

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def runServer(serverAddress, port):
    server = ThreadingHTTPServer((serverAddress, port), RequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    runServer("0.0.0.0", 8080)
