# Twitter Message Mining
Project as part of PhD research at Syracuse University.
Contains code for (i) collecting daily messages using Twitter Streaming API and storing into separate tables in MongoDB and (ii) for each 24 hour time period collected, messages are tokenized and time series analysis used to identify geographic region message belongs to (at the continent level).

Example output from program, visualized using word clouds, where the top 50 tokens are persons (starts with @) or topics (starts with #) for each geographic region (for collection for a day from Dec 2020).
![image](https://user-images.githubusercontent.com/80060152/110036463-0bbd4e00-7d0b-11eb-958d-e9732843b81b.png)

The novel aspect of our approach is that it utilizes the creation times for making these associations. The geo is collected just for comparison purposes. The method also is able to filter out global like tokens that are used worldwide (for example token 'the', 'has', but also '#covid', see paper reference at the end for more details).

# Preliminaries:

Utilizing Ubuntu operating system

Utilizing MongoDB for storing Tweets

Utilizing Python 3.x as the programming language


Python interfaces with MongoDB using pymongo: 

pip install pymongo

Python interfaces with Twitter using tweepy:

pip install tweepy


Important:
Before using the Twitter API you are required to create and register an app (this is free), see:

https://developer.twitter.com/en/docs/twitter-api/getting-started/guide

(By registering an app you will obtain four tokens: consumer key, consumer secret, access token, and access secret. Go inside TwitterAPI.py and put these keys inside getAPI method).

# Collecting Tweets into MongoDB

Create a folder for MongoDB to store info to:
sudo mongod --port 27020 --dbpath '/media/Seagate Expansion Drive/MongoDB/'

    port = 27020
    db_name = "RawTweetCollection"
    from CollectAStreamOfTweets import performRawCollection
    performRawCollection(db_name, port)
