from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from google.cloud import storage, logging_v2 as cloudLogging, pubsub_v1
import json
import mysql.connector
import logging
import sys

cloudLoggingClient = cloudLogging.Client()
cloudLogger = cloudLoggingClient.logger("httpServerLog")
logging.basicConfig(level=logging.INFO)

bannedCountries = ['North Korea', 'Iran', 'Cuba', 'Myanmar', 'Iraq', 'Libya', 'Sudan', 'Zimbabwe', 'Syria']
projectId = 'ds561-bucs'

DB_USER = "root"
DB_PASSWORD = ""

def set_db_credentials(db_host, db_name, pubsub_topic):
    """Sets the database and Pub/Sub topic dynamically."""
    global DB_HOST, DB_NAME, TOPIC_ID
    DB_HOST = db_host
    DB_NAME = db_name
    TOPIC_ID = pubsub_topic

def notifyTrackerApp(country):
    """Publishes a message to Pub/Sub for banned countries."""
    publisher = pubsub_v1.PublisherClient()
    topicPath = publisher.topic_path(projectId, TOPIC_ID)
    messageData = json.dumps({'country': country}).encode('utf-8')
    publisher.publish(topicPath, messageData)
    logging.info(f"Published banned country notification for {country} to Pub/Sub.")

def fetchFileFromBucket(bucketPath):
    """Fetches a file from the GCS bucket."""
    bucketName, filePath = bucketPath.split("/", 1)
    bucket = storage.Client().get_bucket(bucketName)
    blob = bucket.blob(filePath)
    if blob.exists():
        logging.info(f"Fetched file {filePath} from bucket {bucketName}.")
        return blob.download_as_text()
    logging.warning(f"File {filePath} does not exist in bucket {bucketName}.")
    return None

def create_schema_if_not_exists():
    """Creates or verifies the database schema."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        conn.database = DB_NAME

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            country VARCHAR(255) NOT NULL,
            client_ip VARCHAR(255) NOT NULL,
            gender VARCHAR(255) DEFAULT 'unknown',
            age VARCHAR(10) DEFAULT NULL,
            income VARCHAR(255) DEFAULT NULL,
            is_banned BOOLEAN NOT NULL,
            time_of_day VARCHAR(255) DEFAULT NULL,
            requested_file VARCHAR(255) NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            time_req TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            req_file VARCHAR(255) NOT NULL,
            err_code INT NOT NULL
        );
        """)

        conn.commit()
        logging.info("Database schema creation and verification completed.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating schema: {err}")
    finally:
        cursor.close()
        conn.close()

def log_request_to_db(country, client_ip, gender, age, income, is_banned, time_of_day, requested_file):
    """Logs a successful request to the database."""
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file))
        conn.commit()
        logging.info("Request logged successfully.")
    except mysql.connector.Error as err:
        logging.error(f"Error logging request: {err}")
    finally:
        cursor.close()
        conn.close()

def log_error_to_db(requested_file, error_code):
    """Logs a failed request to the database."""
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO failed_requests (req_file, err_code)
            VALUES (%s, %s)
        """, (requested_file, error_code))
        conn.commit()
        logging.info("Error logged successfully.")
    except mysql.connector.Error as err:
        logging.error(f"Error logging error: {err}")
    finally:
        cursor.close()
        conn.close()

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        """Handles GET requests."""
        country = self.headers.get('X-Country', 'unknown')
        client_ip = self.headers.get('X-client-IP', 'unknown')
        gender = self.headers.get('X-gender', 'unknown')
        age = self.headers.get('X-age', 'unknown')
        income = self.headers.get('X-income', 'unknown')
        time_of_day = self.headers.get('X-time', 'unknown')

        is_banned = country in bannedCountries
        if is_banned:
            cloudLogger.log_text(f"Access denied from banned country: {country}", severity="ERROR")
            notifyTrackerApp(country)
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Access denied: Request from banned country")
            log_request_to_db(country, client_ip, gender, age, income, True, time_of_day, self.path)
            log_error_to_db(self.path, 400)
            return

        try:
            fileContent = fetchFileFromBucket(self.path.strip("/"))
            if fileContent is None:
                cloudLogger.log_text(f"File {self.path} not found", severity="ERROR")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
                log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
                log_error_to_db(self.path, 404)
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(fileContent.encode("utf-8"))
                log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
        except Exception as e:
            cloudLogger.log_text(f"Error occurred: {e}", severity="ERROR")
            self.send_response(500)
            self.end_headers()
            log_request_to_db(country, client_ip, gender, age, income, False, time_of_day, self.path)
            log_error_to_db(self.path, 500)

    def handle_unsupported_methods(self):
        """Handles unsupported HTTP methods."""
        cloudLogger.log_text(f"Unsupported method {self.command} was used for {self.path}", severity="ERROR")
        self.send_response(501)
        self.end_headers()
        self.wfile.write(f"{self.command} not implemented".encode("utf-8"))
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
    """Allows the server to handle requests in separate threads."""
    pass

def runServer(serverAddress, port):
    """Starts the HTTP server."""
    logging.info("Starting HTTP server...")
    server = ThreadingHTTPServer((serverAddress, port), RequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        logging.error("Usage: python3 web-server.py <SQL_SERVER_IP> <DB_NAME> <PUBSUB_TOPIC>")
        sys.exit(1)

    logging.info("Setting up database credentials and schema.")
    set_db_credentials(sys.argv[1], sys.argv[2], sys.argv[3])
    create_schema_if_not_exists()
    runServer("0.0.0.0", 8080)
