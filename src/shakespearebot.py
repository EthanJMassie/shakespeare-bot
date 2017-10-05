import tweepy
import configparser
from random import choice
from random import randint
from nltk.corpus import shakespeare
from textblob import TextBlob
import time
import yaml
import datetime

#Initialize parser for reading config file
config = configparser.ConfigParser()

#Read from config file in the above directory
config.read('../config.ini')

#Uses keys defined in the config.ini file to authenticate connection with twitter account
#Don't forget to add your keys to config.ini
auth = tweepy.OAuthHandler(config['OAuth']['public'], config['OAuth']['private'])
auth.set_access_token(config['AccessToken']['public'],config['AccessToken']['private'])

#Initialize Tweepy api with authentication keys
api = tweepy.API(auth)


def main():
    dont_tweet = False
    dont_tweet_till = None
    while True:
        error = False

        if not error and time_range(datetime.time(8, randint(0, 59), 0), datetime.time(22, randint(0, 59), 0))\
                and randint(0, 3) == 2 and not dont_tweet:
            print('Doing some tweeting')
            error = generateTweet()

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)

        print("Follow users")
        error = follow_users()

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)

        #Check for mentions and reply to them
        since_id = config['ID']['since_id']
        while True:
            try:
                mentions = api.search(q='@RealBillyShake' + '-filter:retweets', count=100, since_id=since_id)
                if not mentions:
                    print("No mentions found")
                    break
                for tweet in mentions:
                    if int(tweet.id) > int(since_id):
                        since_id = tweet.id
                        reply_tweets(tweet)

            except tweepy.TweepError as e:
                print("Error: " + str(e))
                break
        config.set('ID', 'since_id', str(since_id))

        with open('../config.ini', 'w') as configfile:
            config.write(configfile)

        if not dont_tweet:
            sleep = randint(120, 14400)
            now = datetime.datetime.now()
            dont_tweet_till = now + datetime.timedelta(seconds=sleep)
            dont_tweet = True
            print('Not tweeting till ' + str(dont_tweet_till.hour) + ':' + str(dont_tweet_till.minute) + ':' + str(dont_tweet_till.second))
        else :
            if(datetime.datetime.now() >= dont_tweet_till):
                dont_tweet = False
            else:
                print('Not tweeting till ' + str(dont_tweet_till.hour) + ':' + str(dont_tweet_till.minute) + ':' + str(dont_tweet_till.second))



def generateTweet():
    files = list(shakespeare.fileids())
    randFile = choice(files)

    play = shakespeare.xml(randFile)

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
                newLine = False
                # Continue adding lines till ending punctuation . or ! or ? is found
                try:

                    while not tweet.endswith('.') or not tweet.endswith('!') or not tweet.endswith('?'):
                        #Check for new line character occurring twice
                        if '\n' in text[y + add] and newLine:
                            break
                        #Check for first occurrence of new line char
                        if '\n' in text[y + add]:
                            newLine = True

                        #If it isn't a new line char add to the tweet
                        if not '\n' in text[y + add]:
                            tweet += ' ' + text[y + add]
                            newLine = False
                        add += 1

                except IndexError:
                    break
                try:
                    # Randomly select if a tweet should be posted and insure proper length
                    if randint(0, 15) == 2 and len(tweet) <= 140 and len(tweet) != 0:
                        print(tweet)
                        api.update_status(tweet)

                        time.sleep(240)
                        return error
                except tweepy.error.RateLimitError:
                    error = True
                    break
    return error


def reply_tweets(mention):
    '''Reply to mentions on twitter'''
    thankful_strings = ['thank you', 'thanks', 'thnx', 'thanketh', 'thx']
    fighting_words = ['roastme', 'roast me', '#roastme']

    #Get sentiment of tweet
    analysis = TextBlob(mention.text)
    sent = analysis.sentiment
    if '?' in mention.text:
        reply = '@' + mention.user.screen_name + " s'rry thee und'rstand not"
        print(reply)
        api.update_status(reply, mention.id)
    elif any(x in mention.text.lower() for x in thankful_strings):
        reply = '@' + mention.user.screen_name +  " thou art welcometh"
        if not mention.favorited:
            api.create_favorite(mention.id)
        print(reply)
        api.update_status(reply, mention.id)
    #Say something mean
    elif sent.polarity < 0.0 or any(x in mention.text.lower() for x in fighting_words):
        #Generate random insult
        insults = yaml.load(open('../insults.yml'))
        insult = '@' + mention.user.screen_name + ' thou art a ' + choice(insults['column1']) + ' ' \
                 + choice(insults['column2']) + ' ' + choice(insults['column3'])
        print(insult)
        api.update_status(insult, mention.id)
    #Say something nice
    elif sent.polarity >= 0.0:
        comps = yaml.load(open('../compliments.yml'))
        compliment = '@' + mention.user.screen_name + ' thou art a ' + choice(comps['column1']) + ' ' \
                 + choice(comps['column2']) + ' ' + choice(comps['column3'])
        print(compliment)
        if not mention.favorited:
            api.create_favorite(mention.id)
        api.update_status(compliment, mention.id)


def delete_tweets():
    '''Deletes 20 most recent tweets'''
    for x in api.user_timeline():
        print("Delete")
        api.destroy_status(x.id)


def follow_users():
    '''Finds users to follow'''
    try:
        count = 0
        #Follow users that follow account
        for follower in api.me().followers():
            if not follower.following:
                api.create_friendship(follower.screen_name)
                print("Now following " + follower.screen_name)
                count += 1
                time.sleep(40)
            time.sleep(20)

        #Limit follows to 10
        if count >= 10:
            return False

        #Follow random users by searching through friends of friends
        for friend in api.me().friends():
            for x in friend.friends():
                if not x.following and x.screen_name != api.me().screen_name:
                    api.create_friendship(x.screen_name)
                    print("Now following " + x.screen_name)
                    count += 1
                if count >= 10:
                    return False
                time.sleep(60)
    except tweepy.error.RateLimitError:
        print("Rate limit reached")
        return True
    except tweepy.error.TweepError as e:
        print("Error: " + str(e) )

    return False


def time_range(start, end):
    '''Stops will from tweeting past bed time'''
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end

main()
