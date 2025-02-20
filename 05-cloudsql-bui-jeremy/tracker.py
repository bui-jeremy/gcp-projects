from google.cloud import pubsub_v1

def callback(message):
    print("Received message from banned country: " + message.data.decode('utf-8'))
    message.ack()

def listenToBannedCountryMessages():
    subscriber = pubsub_v1.SubscriberClient()
    subscriptionPath = subscriber.subscription_path('ds561-bucs', 'banned-country-subscription')
    print("Listening for messages on " + subscriptionPath + "...")
    streamingPullFuture = subscriber.subscribe(subscriptionPath, callback=callback)

    try:
        streamingPullFuture.result()
    except KeyboardInterrupt:
        streamingPullFuture.cancel()

if __name__ == "__main__":
    listenToBannedCountryMessages()
