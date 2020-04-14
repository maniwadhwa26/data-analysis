import json
from os import path

from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener

from sqlalchemy.orm.exc import NoResultFound

from data_analysis.database import session, Tweet, Hashtag, User

consumer_key = '#'
consumer_secret = '#'
access_token = '#'
access_token_secret = '#'


auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


def create_user_helper(user_data):
    # alias to shorten calls
    u = user_data
    user = User(uid=u['id_str'],
                name=u['name'],
                screen_name=u['screen_name'],
                created_at=u['created_at'],
                description=u.get('description'),
                followers_count=u['followers_count'],
                statuses_count=u['statuses_count'],
                favourites_count=u['favourites_count'],
                listed_count=u['listed_count'],
                geo_enabled=u['geo_enabled'],
                lang=u.get('lang')
                )
    return user


def create_tweet_helper(tweet_data, user):
    # alias to shorten calls
    t = tweet_data
    retweet = True if t['text'][:3] == 'RT' else False
    coordinates = json.dumps(t['coordinates'])
    tweet = Tweet(tid=t['id_str'],
                  tweet=t['text'],
                  user=user,
                  coordinates=coordinates,
                  created_at=t['created_at'],
                  favorite_count=t['favorite_count'],
                  in_reply_to_screen_name=t['in_reply_to_screen_name'],
                  in_reply_to_user_id=t['in_reply_to_user_id'],
                  lang=t.get('lang'),
                  quotes_status_id=t.get('quotes_status_id'),
                  retweet_count=t['retweet_count'],
                  source=t['source'],
                  is_retweet=retweet
                  )
    return tweet


def save_to_database(data):
    try:
        user = session.query(User).filter_by(id=str(data['user']['id'])).one()
    except NoResultFound:
        user = create_user_helper(data['user'])
        session.add(user)

    hashtag_results = []
    hashtags = data['entities']['hashtags']
    for hashtag in hashtags:
        hashtag = hashtag['text'].lower()
        try:
            hashtag_obj = session.query(
                Hashtag).filter_by(text=hashtag).one()
        except NoResultFound:
            hashtag_obj = Hashtag(text=hashtag)
            session.add(hashtag_obj)
        hashtag_results.append(hashtag_obj)

    tweet = create_tweet_helper(data, user)
    for hashtag in hashtag_results:
        tweet.hashtags.append(hashtag)

    session.add(tweet)
    session.commit()


def _get_dir_absolute_path():
    """
    helper method to get the absoulte path of the file directory
    """
    directory = path.abspath(path.dirname(__file__))
    return directory


def save_tweets():
    directory = _get_dir_absolute_path()
    filepath = path.join(directory, 'tweets.json')

    listener = DatabaseListener(number_tweets_to_save=1000, filepath=filepath)

    stream = Stream(auth, listener)
    languages = ('en',)
    try:
        stream.sample(languages=languages)
    except KeyboardInterrupt:
        listener.file.close()


class DatabaseListener(StreamListener):
    def __init__(self, number_tweets_to_save, filepath=None):
        self._final_count = number_tweets_to_save
        self._current_count = 0
        if filepath is None:
            filepath = 'tweets.txt'
        self.file = open(filepath, 'w')

    # Note : Slightly dangerous due to circular refernces
    def __del__(self):
        self.file.close()

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        json.dump(raw_data, self.file)
        self.file.write('\n')
        if 'in_reply_to_status_id' in data:
            return self.on_status(data)

    def on_status(self, data):
        # Note: THis method is define in the file
        save_to_database(data)

        self._current_count += 1
        print('Status Count: {}'.format(self._current_count))
        if self._current_count >= self._final_count:
            return False


if __name__ == '__main__':
    save_tweets()
