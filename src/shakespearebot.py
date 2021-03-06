import tweepy
import configparser
from random import choice
from random import randint
from nltk.corpus import shakespeare
from textblob import TextBlob
import time
import yaml
import datetime
import sys

# Initialize parser for reading config file
config = configparser.ConfigParser()

# Read from config file in the above directory
config.read('../config.ini')

# Checks if config file has the proper information/exists
# If not creates a template for the config file
auth = tweepy.OAuthHandler
try:
    auth = tweepy.OAuthHandler(config['OAuth']['public'], config['OAuth']['private'])
    auth.set_access_token(config['AccessToken']['public'], config['AccessToken']['private'])
except KeyError:
    print("No config.ini file present\nCreating new config.ini file...")

    config.add_section('OAuth')
    config.set('OAuth', 'public', '')
    config.set('OAuth', 'private', '')
    config.add_section('AccessToken')
    config.set('AccessToken', 'public', '')
    config.set('AccessToken', 'private', '')
    config.add_section("ID")
    config.set("ID", 'since_id', '')
    config.add_section('Limits')
    config.set('Limits', 'dont_tweet_till', str(datetime.datetime.now()))
    config.set('Limits', 'dont_tweet', 'False')
    config.set('Limits', 'dont_follow_till', str(datetime.datetime.now()))
    config.set('Limits', 'dont_follow', 'False')
    config.set('Limits', 'recent_status_up', 'False')
    with open('../config.ini', 'w') as configfile:
        config.write(configfile)
    print("Add your twitter key values to config.ini file before running the program")
    sys.exit(1)

# Initialize Tweepy api with authentication keys
api = tweepy.API(auth)


def main():
    # Set limit values from config file
    dont_tweet = str_to_bool(config['Limits']['dont_tweet'])
    dont_tweet_till = datetime.datetime.strptime(config['Limits']['dont_tweet_till'], "%Y-%m-%d %H:%M:%S.%f")
    recent_status_up = str_to_bool(config['Limits']['recent_status_up'])
    dont_follow = str_to_bool(config['Limits']['dont_follow'])
    dont_follow_till = datetime.datetime.strptime(config['Limits']['dont_follow_till'], "%Y-%m-%d %H:%M:%S.%f")

    print('Not following till ' + str(dont_follow_till))
    print('Not tweeting till ' + str(dont_tweet_till))
    while True:
        rate_limit = False
        follow_error = False

        if time_range(datetime.time(8, randint(0, 59), 0), datetime.time(22, randint(0, 59), 0)) \
                and randint(0, 3) == 2 and not dont_tweet:
            print('Doing some tweeting')
            return_tuple = generate_tweet()
            rate_limit = return_tuple[0]
            recent_status_up = return_tuple[1]

        if rate_limit:
            print("Rate limit reached cooling off for a bit")
            time.sleep(360)

        if not dont_follow:
            print("Follow users")
            errors = follow_users()
            rate_limit = errors[0]
            follow_error = errors[1]

        if rate_limit:
            print("Rate limit reached cooling off for a bit")
            rate_limit = False
            time.sleep(360)

        # Check for mentions and reply to them
        since_id = config['ID']['since_id']
        while True:
            try:
                mentions = api.search(q='@RealBillyShake' + '-filter:retweets', since_id=since_id)
                if mentions is None:
                    print("No mentions found")
                    break
                else:
                    for tweet in mentions:
                        if int(tweet.id) > int(since_id):
                            since_id = tweet.id
                            reply_tweets(tweet)

            except tweepy.TweepError as e:
                print("Error: " + str(e))
                rate_limit = True
                break

        # Store new since_id in config
        config.set('ID', 'since_id', str(since_id))

        with open('../config.ini', 'w') as configfile:
            config.write(configfile)

        if rate_limit:
            print("Rate limit reached cooling off for a bit")
            time.sleep(360)

        # Stop tweeting till a random amount of time has past
        if not dont_tweet and recent_status_up:
            now = datetime.datetime.now()
            dont_tweet_till = now + datetime.timedelta(seconds=randint(3600 * 6, 3600 * 16))
            dont_tweet = True
            recent_status_up = False
            print('Not tweeting till ' + str(dont_tweet_till))

            # Store new limits in config
            config.set('Limits', 'dont_tweet_till', str(dont_tweet_till))
            config.set('Limits', 'dont_tweet', 'True')
            config.set('Limits', 'recent_status_up', 'False')
            with open('../config.ini', 'w') as configfile:
                config.write(configfile)
        else:
            if datetime.datetime.now() >= dont_tweet_till:
                dont_tweet = False
                config.set('Limits', 'dont_tweet', 'False')
                with open('../config.ini', 'w') as configfile:
                    config.write(configfile)
            else:
                print('Not tweeting till ' + str(dont_tweet_till))

        # Stop following for a week if an rate_limit is returned from follow_users
        if not dont_follow and follow_error:
            now = datetime.datetime.now()
            dont_follow_till = now + datetime.timedelta(days=7)
            dont_follow = True
            print('Not following till ' + str(dont_follow_till))

            # Store new limits in config
            config.set('Limits', 'dont_follow_till', str(dont_follow_till))
            config.set('Limits', 'dont_follow', 'True')
            with open('../config.ini', 'w') as configfile:
                config.write(configfile)
        elif dont_follow:
            if datetime.datetime.now() >= dont_follow_till:
                dont_follow = False
                config.set('Limits', 'dont_follow', 'False')
                with open('../config.ini', 'w') as configfile:
                    config.write(configfile)
            else:
                print('Not following till ' + str(dont_follow_till))

        time.sleep(120)


def generate_tweet():
    files = list(shakespeare.fileids())
    rand_file = choice(files)

    play = shakespeare.xml(rand_file)

    characters = list(speaker.text for speaker in play.findall('*/*/*/SPEAKER'))
    character = choice(characters)

    error = False
    # loop through text of the selected play
    for x in play:
        if error:
            break
        text = list(x.itertext())
        for y in range(0, len(text) - 1):
            # Find text that matches the selected characters name
            if text[y].lower() == character.lower():
                # Add this characters lines to the tweet
                add = 2
                tweet = ''
                tweet += text[y + add]
                add += 1
                new_line = False
                # Continue adding lines till ending punctuation . or ! or ? is found
                try:

                    while not tweet.endswith('.') or not tweet.endswith('!') or not tweet.endswith('?'):
                        # Check for new line character occurring twice
                        if '\n' in text[y + add] and new_line:
                            break
                        # Check for first occurrence of new line char
                        if '\n' in text[y + add]:
                            new_line = True

                        # If it isn't a new line char add to the tweet
                        if '\n' not in text[y + add]:
                            tweet += ' ' + text[y + add]
                            new_line = False
                        add += 1

                except IndexError:
                    break
                try:
                    # Randomly select if a tweet should be posted and insure proper length
                    if randint(0, 15) == 2 and len(tweet) <= 140 and len(tweet) != 0:
                        print(tweet)
                        api.update_status(tweet)

                        time.sleep(240)
                        return error, True
                except tweepy.error.RateLimitError:
                    error = True
                    break
    return error, False


def reply_tweets(mention):
    ''' Reply to mentions on twitter '''

    # Lists of keywords
    thankful_strings = ['thank you', 'thanks', 'thnx', 'thanketh', 'thx']
    fighting_words = ['roastme', 'roast me', '#roastme']
    questions = ['who', '?', 'what', 'how', 'when', 'where']

    # Reply lists
    question_replies = [" Thou w're not meanteth to und'rstand", " s'rry thee und'rstand not",
                        " wherefore art thou confused?"]
    youre_welcome = [" 't is nay problem", " thou art welcome", " 't is mine pleasure"]

    # Get sentiment of tweet
    analysis = TextBlob(mention.text)
    sent = analysis.sentiment

    # Reply to a question
    if any(x in mention.text.lower() for x in questions):
        reply = '@' + mention.user.screen_name + choice(question_replies)
        print(reply)
        api.update_status(reply, mention.id)
        return
    # Say you're welcome if they thank him
    elif any(x in mention.text.lower() for x in thankful_strings):
        reply = '@' + mention.user.screen_name + choice(youre_welcome)
        if not mention.favorited:
            api.create_favorite(mention.id)
        print(reply)
        api.update_status(reply, mention.id)
        return

    # Say something mean
    if sent.polarity < 0.0 or any(x in mention.text.lower() for x in fighting_words):
        # Generate random insult
        insults = yaml.load(open('../insults.yml'))
        insult = '@' + mention.user.screen_name + ' thou art a ' + choice(insults['column1']) + ' ' \
                 + choice(insults['column2']) + ' ' + choice(insults['column3'])
        print(insult)
        api.update_status(insult, mention.id)
    # Say something nice
    elif sent.polarity >= 0.0:
        comps = yaml.load(open('../compliments.yml'))
        compliment = '@' + mention.user.screen_name + ' thou art a ' + choice(comps['column1']) + ' ' \
                     + choice(comps['column2']) + ' ' + choice(comps['column3'])
        print(compliment)
        if not mention.favorited:
            api.create_favorite(mention.id)
        api.update_status(compliment, mention.id)


def delete_tweets():
    ''' Deletes 20 most recent tweets '''
    for x in api.user_timeline():
        print("Delete")
        api.destroy_status(x.id)


def follow_users():
    '''Finds users to follow'''
    try:
        count = 0
        already_following = 0
        # Follow users that follow account
        for follower in api.me().followers():
            if not follower.following:
                api.create_friendship(follower.screen_name)
                print("Now following " + follower.screen_name)
                count += 1
                time.sleep(40)
            else:
                already_following += 1
                time.sleep(40)
            if already_following >= 20:
                break
            time.sleep(20)

        # Limit follows to 10
        if count >= 10:
            return False, False

        # Follow random users by searching through friends of friends
        for friend in api.me().friends():
            for x in friend.friends():
                if not x.following and x.screen_name != api.me().screen_name:
                    api.create_friendship(x.screen_name)
                    print("Now following " + x.screen_name)
                    count += 1
                if count >= 10:
                    return False, False
                time.sleep(60)
    except tweepy.error.RateLimitError:
        return True, False
    except tweepy.error.TweepError as e:
        print("Error: " + str(e))
        return False, True

    return False, False


def time_range(start, end):
    ''' Stops will from tweeting past bed time '''
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False

    return False


main()
