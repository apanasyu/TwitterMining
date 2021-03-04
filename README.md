# Twitter Message Mining
Project as part of PhD research at Syracuse University.
Contains code for (i) collecting daily messages using Twitter Streaming API and storing into separate tables in MongoDB and (ii) for each 24 hour time period collected, messages are tokenized and time series analysis used to identify geographic region message belongs to (at the continent level).

Example output from program, visualized using word clouds, where the top 50 tokens are persons (starts with @) or topics (starts with #) for each geographic region (for collection for a day from Dec 2020).
![image](https://user-images.githubusercontent.com/80060152/110036463-0bbd4e00-7d0b-11eb-958d-e9732843b81b.png)

The novel aspect of our approach is that it utilizes the creation times for making these associations. The geo is collected just for comparison purposes. The method also is able to filter out global like tokens that are used worldwide (for example token 'the', 'has', but also '#covid', see paper reference at the end for more details).

# Preliminaries:

Utilizing Ubuntu operating system, MongoDB for storing Tweets, Python 3.x as the programming language.

Python interfaces with MongoDB using pymongo (pip install pymongo), with Twitter using tweepy (pip install tweepy).

Important:
Before using the Twitter API you are required to create and register your app (this is free), see:

https://developer.twitter.com/en/docs/twitter-api/getting-started/guide

(By registering an app you will obtain four tokens: consumer key, consumer secret, access token, and access secret. Go inside TwitterAPI.py and put these keys inside getAPI method).

# Collecting Tweets into MongoDB

Step 1:
Create a folder for MongoDB to store info to:
sudo mongod --port 27020 --dbpath '/media/Seagate Expansion Drive/MongoDB/'

Step 2:
Inside Main.py:

    port = 27020
    db_name = "RawTweetCollection"
    from CollectAStreamOfTweets import performRawCollection
    performRawCollection(db_name, port)

This will create a database called  RawTweetCollection. Tweets using the Streaming API will be collected into Table Day1 (program will notify everytime a write is done). After 24 hours the tweets will go to Table Day2. After 24 hours to Table Day 3. And so on …
The method will keep collecting tweets until terminated.

Each 24 hour period will result in a Table with a couple million tweets. Each table will be around 1 GB.
Below is a screenshot using MongoDB Compass:
![image](https://user-images.githubusercontent.com/80060152/110038400-b5054380-7d0d-11eb-9c4d-d196de3050cb.png)

For each message we record the message id, text, user screenName that created it, the creation time. We also record any available geo in the form of place or coordinates from message and the user’s self-reported location from user (if such info is available):

![image](https://user-images.githubusercontent.com/80060152/110038450-c4848c80-7d0d-11eb-9559-d11290167c29.png)

Messages with geo will be typically < 1%:

![image](https://user-images.githubusercontent.com/80060152/110038494-d1a17b80-7d0d-11eb-9cf3-183ec88fcfa7.png)

