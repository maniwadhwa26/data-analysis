from tweepy import OAuthHandler, Stream, API
import json
from tweepy.streaming import StreamListener

consumer_key = '#'
consumer_secret = '#'
access_token = '#'
access_token_secret = '#'


auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


class PrintListener(StreamListener):
    def on_status(self, status):
        if not status.text[:3] == 'RT ':
            print(status.text)
            print(status.author.screen_name,
                  status.created_at, status.source, '\n')

    def on_error(self, status_code):
        print("Error Code:{}".format(status_code))

    def on_timeout(self):
        print("Listener Timed Out")
        return True  # Keep Stream Live


def print_to_terminal():
    listener = PrintListener()
    stream = Stream(auth, listener)
    languages = ('en',)
    stream.sample(languages=languages)


def pull_down_tweets(screen_name):
    api = API(auth)
    tweets = api.user_timeline(screen_name=screen_name, counts=200)
    for tweet in tweets:
        print(json.dumps(tweet._json, indent=4))


if __name__ == '__main__':
    # print_to_terminal()
    pull_down_tweets(auth.username)
