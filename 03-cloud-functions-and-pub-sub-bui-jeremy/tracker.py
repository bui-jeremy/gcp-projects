from google.cloud import pubsub_v1

project_id = 'ds561-bucs'
subscription_id = 'banned-country-subscription'

def callback(message):
    print('Received message from banned country: ' + message.data.decode('utf-8'))
    message.ack()

def listen_to_banned_country_messages():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    print('Listening for messages on ' + subscription_path + '...\n')

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()

if __name__ == '__main__':
    listen_to_banned_country_messages()