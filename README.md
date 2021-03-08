# Twitter Message Mining
Project as part of PhD research at Syracuse University.
Contains code for (i) collecting daily messages using Twitter Streaming API and storing into separate tables in MongoDB and (ii) for each 24 hour time period collected, messages are tokenized and time series analysis used to identify geographic region message belongs to (at the continent level).

Example output from program, visualized using word clouds, where the top 50 tokens are persons (starts with @) or topics (starts with #) for each geographic region (for collection for a day from Dec 2020).

<img src="https://user-images.githubusercontent.com/80060152/110036463-0bbd4e00-7d0b-11eb-958d-e9732843b81b.png" width="800">

The novel aspect of our approach is that it utilizes the creation times for making these associations. The geo is collected just for comparison purposes. The method also is able to filter out global like tokens that are used worldwide (for example token 'the', 'has', but also '#covid', see paper reference at the end for more details).

# Preliminaries:

Utilizing Ubuntu operating system, MongoDB for storing Tweets, Python 3.x as the programming language.

Python interfaces with MongoDB using pymongo (pip install pymongo), with Twitter using tweepy (pip install tweepy). Other library dependencies: numpy, scipy, nltk, WordCloud.

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

Step 1: Form Time Distribution
The database and table pairs that we want to analyze are sent to the method analyzeTokensInTables (in this way can focus on message traffic over multiple 24-hour periods). This method utilizes the NLTK library for tokenizing each tweet (from nltk.tokenize import TweetTokenizer). The hour from the creation time of the message is used. For each token we generate a time distribution (a normalized histogram with 24 bins one for each hour) that captures how likely the messages, associated with the token, were to be created at any hour.

<img src="https://user-images.githubusercontent.com/80060152/110215537-59a39480-7e78-11eb-89bf-2fe6d028995d.png" width="600">

Second, instead of message creation times, the creation times associated with the users that had created the messages can be utilized to form a time distribution (when focussing on users we ensure that each user appears only once; whereas for message traffic it is possible that multiple messages originate from the same user). The time distribution for each token is stored in a temporary database Temp_Analysis using Tables: (i) TimeDist_Combined using message creation times and (ii) TimeDist_Combined_AtUser using user creation times.

Step 2: Use Time Distribution to predict UTC

Each time distribution is processed as such: (i) 24 hour time distribution repeated over 48 hour period (in blue), (ii) moving average n=5 used to achieve smoothness (in green), (iii) the start and end of the sleep cycle are the intersection points with a negative and positive slope below 33th percentile (in orange). Sleep portion expected to occupy a single continuous segment with three to four intersection points per 48 hours. A polynomial is fitted to the sleep cycle: f(t) = c0 + c1 * t + c2 * t2. If it is a U-shaped parabola, the min is used for predicting the UTC offset of the geographic area that the message most likely originates from.

Figure below is an example of two time distributions (notice the U-shape valley below the 33th percentile in each).

<img src="https://user-images.githubusercontent.com/80060152/110045806-3a422580-7d19-11eb-8c29-c8e864ba3447.png" width="500">

The time distribution analysis for each token is stored in a temporary database Temp_Analysis using Tables: (i) TokenTimeFeaturesProcessed using message creation times and (ii) TokenTimeFeaturesProcessedUser using user creation times. Here is the info in MongoDB after processing a collection over 24 hours.

![image](https://user-images.githubusercontent.com/80060152/110257922-0c095380-7f6e-11eb-8337-59a4418c8411.png)

Note: not all tokens had a time distribution for which a U-shaped parabola could be used to predict UTC (out of 9246 messages 8008 contained a UTC prediction).

Step 3: UTC used to associate to one of three high-level geographic regions

    from Step3AnalyzeTokens import getTokenToRegion
    rSquareT = 0.85
    minRecordT = 500
    powerC2T = 0.001
    atUser = False
    americas, africaEurope, asiaAustralia = getTokenToRegion(port, atUser, rSquareT, minRecordT, powerC2T)

The MongoDB tables are returned as Pandas DataFrames. We filter the DataFrame to those tokens with high confidence UTC predictions, where (i) polynomial fitted over sleep cycle has R^2 over 0.85, (ii) time distribution contains at least 500 creation times, (iii) power coefficient c2 > 0.001 (indicating strong U-shape). 

The method getTokenToRegion assigns region based on UTC prediction.

<img src="https://user-images.githubusercontent.com/80060152/110258307-f72dbf80-7f6f-11eb-8423-c81c5b219c67.png" width="500">

# C. Form Visualizations

    df = asiaAustralia
    tokens = set(list(df["id"]))
    tokenPersonTopic = set([])
    for token in tokens:
        if len(token) > 1:
            if token.startswith('@') or token.startswith('#'):
                tokenPersonTopic.add(token)

    df = df.loc[df['id'].isin(list(tokenPersonTopic))]
    N = 50
    topN = list(df.nlargest(N, 'totalRecords')["id"])
    topNDF = df.loc[df['id'].isin(topN)]
    tokenToCount = dict(zip(list(df["id"]), list(df['totalRecords'])))

    from step4Visualize import formWordCloud
    formWordCloud(tokenToCount, "Asia_Oceania_WordCloud", outputDir)

This example uses tokens associated with Asia/Oceania. The focus is on tokens that are known person or topic (on Twitter @ and # have this special meaning). The top 50 tokens are visualized in a WordCloud (this WordCloud generated using collection on 03/05/2021).

<img src="https://user-images.githubusercontent.com/80060152/110348403-9d74d600-7fff-11eb-9af8-3acc0727efa1.png" width="200">

In Pandas it is possible to quickly analyze any specific time distribution(s). For example, for Asia/Oceania the top 10 tokens are used to generate a box plot that shows the typical time distribution has a lack of activity during hours (0-1 and 18-23) via following code:

<img src="https://user-images.githubusercontent.com/80060152/110263117-acb63e00-7f83-11eb-8b3b-f652bcb8a1ec.png" width="400">

    import matplotlib.pyplot as plt 
    db_name = "Temp_Analysis"
    collectionTimeDistMessage = "TimeDist_Combined"
    collectionTimeDistUser = "TimeDist_Combined_AtUser"
    collectionTimeFeaturesMessage = "TokenTimeFeaturesProcessed"
    collectionTimeFeaturesUser = "TokenTimeFeaturesProcessedUser"

    from MongoDBInterface import getMongoIntoPandas
    df = getMongoIntoPandas(port, db_name, collectionTimeDistMessage, None)
    print df
    df = df.loc[df['_id'].isin(topN)]
    hours = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    normalizedTimeDistDF = df[hours].div(df[hours].sum(axis=1), axis=0)
    df = normalizedTimeDistDF.dropna()    
    df = df[hours]
    df.plot.box()
    plt.show()

# D. Associations using Geo

For evaluation purposes we also assign a label based on the geo found in messages. Geo is in the form of point coordinates as well as place which specifies coordinates via a bounding box. The following used to assign a label:

<img src="https://user-images.githubusercontent.com/80060152/110343247-4c161800-7ffa-11eb-908d-ac5cd9ec2c89.png" width="500">

For coordinates specified using a bounding box, both the longitude components had to be associated with the same region. A token is assigned a label based on the region which captured the biggest ratio of messages. For example, here are the top 20 person/topic tokens and associated label (the last column shows number of messages with geo used in determining label). Table based on a single 24 hour collection of tweets, the more collections the higher the confidence in the labels.

![image](https://user-images.githubusercontent.com/80060152/110351170-8be0fd80-8002-11eb-9d4f-e3366ed4490d.png)

The following code generates labels for all tokens that are contained in messages with geo:

    tokenToCoordinates3Div(db_nameAndCollection, port)
    formCSVFromGeoInMessages(outputDir, port)

The labels via Geo can be compared against the labels formed using temporal features. From the book chapter, using a collection over 5 days the table shows how the two compare (where NA_SA = Americas, AF_EUR = Europe/Africa, and AS_OC = Asia/Oceania). The first row, with no restriction, illustrates that if a UTC prediction is made it generally has good accuracy. The accuracy is high, particularly for those tokens which have ground truth assembled from more messages (larger x) and with high confidence UTC predictions (high $R^2$ and $c_2$). 

![image](https://user-images.githubusercontent.com/80060152/110351449-d6fb1080-8002-11eb-9f05-6f8f91a677ec.png)

