# Twitter Message Mining
Project as part of PhD research at Syracuse University.
Contains code for (i) collecting daily messages using Twitter Streaming API and storing into separate tables in MongoDB and (ii) for each 24 hour time period collected, messages are tokenized and time series analysis used to identify geographic region message belongs to (at the continent level).

Example output from program, visualized using word clouds, where the top 50 tokens are persons (starts with @) or topics (starts with #) for each geographic region (for collection for a day from Dec 2020).
![image](https://user-images.githubusercontent.com/80060152/110036463-0bbd4e00-7d0b-11eb-958d-e9732843b81b.png)

The novel aspect of our approach is that it utilizes the creation times for making these associations. The geo is collected just for comparison purposes. The method also is able to filter out global like tokens that are used worldwide (for example token 'the', 'has', but also '#covid', see paper reference at the end for more details).

# Preliminaries:

Utilizing Ubuntu operating system, MongoDB for storing Tweets, Python 3.x as the programming language.

Python interfaces with MongoDB using pymongo (pip install pymongo), with Twitter using tweepy (pip install tweepy). Other library dependencies: numpy, scipy, nltk.

Important:
Before using the Twitter API you are required to create and register your app (this is free), see:

https://developer.twitter.com/en/docs/twitter-api/getting-started/guide

(By registering an app you will obtain four tokens: consumer key, consumer secret, access token, and access secret. Go inside TwitterAPI.py and put these keys inside getAPI method).

# A. Collecting Tweets into MongoDB

Step 1:
Create a folder for MongoDB to store info to:
sudo mongod --port 27020 --dbpath '/media/user1/Seagate Expansion Drive/MongoDB/'

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

For each message we record: (i) related to message: id, text, creation time and (ii) related to user that created the message: id, screenName, creation time. We also record any available geo in the form of place or coordinates from message and the user’s self-reported location from user:

![image](https://user-images.githubusercontent.com/80060152/110140965-a74dcd80-7da2-11eb-9ae5-893aa59e2952.png)

Messages with geo will be typically < 1%:

![image](https://user-images.githubusercontent.com/80060152/110141459-2b07ba00-7da3-11eb-85bf-b7d0792e8d76.png)

# B. Process Table(s) containing 24 hours of tweets

    port = 27020
    outputDir = "/media/user1/Seagate Expansion Drive/temp/"
    minFreq = 500
    db_nameAndCollection = [["RawTweetCollection", "Day1"], ["RawTweetCollection", "Day2"]]
    from Step2ProcessTableOfTweets import analyzeTokensInTables
    analyzeTokensInTables(db_nameAndCollection, minFreq, outputDir, port)

The database and table pairs that we want to analyze are sent to the method analyzeTokensInTables (in this way can focus on message traffic over multiple 24-hour periods). This method utilizes the NLTK library for tokenizing each tweet (from nltk.tokenize import TweetTokenizer). The hour from the creation time of the message is used. For each token we generate a time distribution (a normalized histogram with 24 bins one for each hour) that captures how likely the messages, associated with the token, were to be created at any hour.

![image](https://user-images.githubusercontent.com/80060152/110215537-59a39480-7e78-11eb-89bf-2fe6d028995d.png)

In the same fashion the creation times associated with the users that had created the messages can be utilized to form a time distribution (when focussing on users we ensure that each user appears only once; whereas for message traffic it is possible that multiple messages originate from the same user). The time distribution for each token is stored in a temporary database Temp_Analysis using Tables: (i) TimeDist_Combined using message creation times and (ii) TimeDist_Combined_AtUser using user creation times.

The output directory will also store the CSV files.  



Each time distribution is processed as such: (i) 24 hour time distribution repeated over 48 hour period (in blue), (ii) moving average n=5 used to achieve smoothness (in green), (iii) the start and end of the sleep cycle are the intersection points with a negative and positive slope below 33th percentile (in orange). Sleep portion expected to occupy a single continuous segment with three to four intersection points per 48 hours. A polynomial is fitted to the sleep cycle: f(t) = c0 + c1 * t + c2 * t2. If it is a U-shaped parabola, the min is used for predicting the UTC offset of the geographic area that the message most likely originates from.

Figure below is an example of two time distributions (notice the U-shape valley below the 33th percentile in each).

![image](https://user-images.githubusercontent.com/80060152/110045806-3a422580-7d19-11eb-8c29-c8e864ba3447.png)

The table(s) for which collection is complete can be used to process all tokens that appear at least x times (captured by the minFreq variable).



