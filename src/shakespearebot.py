import tweepy
import configparser
from random import randint
from nltk.corpus import shakespeare
import time
import datetime

#Initialize parser for reading config file
config = configparser.ConfigParser()

#Read from config file in the above directory
config.read('../keys.ini')

#Uses keys defined in the keys.ini file to authenticate connection with twitter account
#Don't forget to add your keys to keys.ini
auth = tweepy.OAuthHandler(config['OAuth']['public'], config['OAuth']['private'])
auth.set_access_token(config['AccessToken']['public'],config['AccessToken']['private'])

#Initialize Tweepy api with authentication keys
api = tweepy.API(auth)


def main():

    while True:
        count = 0
        error = False

        while count < randint(1, 10) and not error \
                and time_range(datetime.time(randint(6, 9), randint(0, 59), 0), datetime.time(rand_list_item([0, 23, 22]), randint(0, 59), 0)):
            returned_tuple = generateTweet(randint(1, 3))
            count += returned_tuple[0]
            error = returned_tuple[1]

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)

        print("Follow users")
        error = follow_users()

        if error:
            print("Rate limit reached\nCooling off...")
            time.sleep(120)






def generateTweet(limit):
    files = list(shakespeare.fileids())
    randFile = rand_list_item(files)

    play = shakespeare.xml(randFile)

    characters = list(speaker.text for speaker in play.findall('*/*/*/SPEAKER'))
    character = rand_list_item(characters)

    tweetcount = 0
    error = False
    # loop through text of the selected play
    for x in play:
        if error:
            break
        text = list(x.itertext())
        for y in range(0, len(text) - 1):
            # Find text that matches the selected characters name
            if text[y].lower() == character.lower() and tweetcount < limit:
                # Add this characters lines to the tweet
                add = 2
                tweet = ''
                tweet += text[y + add]
                add += 1
                newLine = False
                # Continue adding lines till ending punctuation . or ! is found
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
                    pass
                try:
                    # Randomly select if a tweet should be posted and insure proper length
                    if randint(0, 7) == 2 and len(tweet) <= 140 and len(tweet) != 0:
                        print(tweet)
                        api.update_status(tweet)
                        tweetcount += 1
                        time.sleep(randint(240, 28800))
                except tweepy.error.RateLimitError:
                    error = True
                    break
    return tweetcount, error


def delete_tweets():
    '''Deletes 20 most recent tweets'''
    for x in api.user_timeline():
        print("Delete")
        api.destroy_status(x.id)


def follow_users():
    '''Finds random users to follow'''
    try:
        for friend in api.me().friends():
            for x in friend.friends():
                if not x.following:
                    print("Now following " + x.screen_name)
                    api.create_friendship(x.screen_name)
                time.sleep(60)
    except tweepy.error.RateLimitError:
        return True

    return False


def time_range(start, end):
    '''Stops will from tweeting past bed time'''
    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end

def rand_list_item(list):
    return list[randint(0, len(list) - 1)]
main()