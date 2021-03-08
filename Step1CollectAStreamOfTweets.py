import sys
from tweepy.streaming import StreamListener
import json
from datetime import datetime
collectionName = None
count = 0
infoToWrite = []
db = None
port = None

class listener(StreamListener):
    def on_data(self, data):
        global infoToWrite
        global count
        global db
        global collectionName
        all_data = json.loads(data)

        if 'id_str' in all_data:
            d = {}
            if all_data["coordinates"] != None:
                d['coordinatesPoint'] = all_data["coordinates"]

            if all_data["place"] != None:
                d['place'] = all_data["place"]

            id_str = all_data["id_str"]
            tweetOriginal = all_data["text"]
            created_at = transformTwitterDateStringToProperDateTime(all_data["created_at"])
            tHour = created_at.hour
            created_at2 = transformTwitterDateStringToProperDateTime(all_data["user"]["created_at"])
            tHour2 = created_at2.hour
            username = all_data["user"]["screen_name"]
            user_id_str = all_data["user"]["id_str"]
            if all_data["user"]["location"] != None:
                d["selfreportedUserLocation"] = all_data["user"]["location"]
            try:
                lang = all_data["lang"]
            except:
                lang = ""

            d['_id'] = id_str
            d['user_id'] = user_id_str
            d["tweetOriginal"] = tweetOriginal
            d["lang"] = lang
            d["created_at"] = created_at
            d["tHour"] = tHour
            d["created_at_user"] = created_at2
            d["tHour2"] = tHour2
            d["username"] = username
            infoToWrite.append(d)

            if len(infoToWrite) > 250:
                try:
                    db[collectionName].insert_many(infoToWrite, ordered=False)
                    infoToWrite = []
                    count += 1
                    print("Performed write " + str(count))
                except:
                    infoToWrite = []
                    print("Error when doing bulk write")

        return(True)

    def on_error(self, status):
        print(status)
    
    def on_status(self, status):
        print(status.text)

def transformTwitterDateStringToProperDateTime(twitterDateString):
    return datetime.strptime(twitterDateString,'%a %b %d %H:%M:%S +0000 %Y')

def performRawCollection(db_name, portIn):
    port = portIn
    global db
    global collectionName
    from tweepy import Stream
    from TwitterAPI import getAPI
    twitterAPI1 = getAPI()
    twitterStream = Stream(auth=twitterAPI1.auth, listener=listener())
    
    from MongoDBInterface import getMongoClient
    client = getMongoClient(port)
    db = client[db_name]
    collectionName = "Day1"
    
    print("Start day 1. " + "Writing to:" + db_name + "," + str(collectionName))

    twitterStream.sample(async=True)
    import time
    dayCount = 2
    while True:
        time.sleep(86400)
        print("Finished collection for day:" + str(dayCount-1))
        print("Starting day " + str(dayCount))
        collectionName = "Day"+str(dayCount)
        print("Start day " + str(dayCount) + ". Writing to:" + db_name + "," + str(collectionName))
        dayCount += 1