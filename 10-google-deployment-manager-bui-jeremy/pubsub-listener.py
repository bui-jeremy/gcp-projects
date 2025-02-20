from google.cloud import pubsub_v1
from google.cloud import logging
import sys

PROJECT_ID = 'ds561-bucs'

logging_client = logging.Client()
log_name = "banned-country-listener"
logger = logging_client.logger(log_name)

def callback(message):
    log_entry = f"Received message from banned country: {message.data.decode('utf-8')}"
    print(log_entry)
    logger.log_text(log_entry)
    message.ack()

def listenToBannedCountryMessages(subscription_name):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, subscription_name)
    start_log = f"Listening for messages on {subscription_path}..."
    print(start_log)
    logger.log_text(start_log)
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        stop_log = "Listener interrupted by user (KeyboardInterrupt)."
        print(stop_log)
        logger.log_text(stop_log)
        streaming_pull_future.cancel()
    except Exception as e:
        error_log = f"Error occurred in listener: {e}"
        print(error_log)
        logger.log_text(error_log)
    finally:
        print("Shutting down listener...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage_log = "Usage: python3 listener.py <SUBSCRIPTION_NAME>"
        print(usage_log)
        logger.log_text(usage_log)
        sys.exit(1)

    subscription_name = sys.argv[1]
    listenToBannedCountryMessages(subscription_name)
