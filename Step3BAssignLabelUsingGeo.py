def tokenToCoordinates3Div(db_nameAndCollection, portInput):
    from Step2ProcessTableOfTweets import processString
    from MongoDBInterface import getMongoClient
        
    errorCounts = 0
    tokenToCoordinate = {}
    for pair in db_nameAndCollection:
        db_name = pair[0]
        collectionName = pair[1]
        
        client = getMongoClient(portInput)
        db = client[db_name]
        
        collectionToRead = db[collectionName]
        query = {}
        fields = {'tweetOriginal':1, 'coordinatesPoint':1, 'place':1}
        tweetCursor = collectionToRead.find(query, fields, no_cursor_timeout=True)
        
        for userInfo in tweetCursor:
            label = None
            if 'coordinatesPoint' in userInfo:
                long = userInfo['coordinatesPoint']['coordinates'][0]
                if long <= -25:
                    label = -1
                elif long <= 65:
                    label = 0
                else:
                    label = 1
            elif 'place' in userInfo:
                longs = []
                for coordinatePair in userInfo['place']['bounding_box']['coordinates'][0]:
                    longs.append(coordinatePair[0])
                
                l1 = 0
                l2 = 0
                l3 = 0
                for long in longs:
                    if long <= -25:
                        l1 += 1
                    elif long <= 65:
                        l2 += 1
                    else:
                        l3 += 1
                if l1 == 4:
                    label = -1
                elif l2 == 4:
                    label = 0
                elif l3 == 4:
                    label = 1
                else:
                    print(str(errorCounts) + " " + str(userInfo['place']))
                    errorCounts += 1

            if label != None:
                tokens = processString(userInfo["tweetOriginal"])
                for token in tokens:
                    if not token in tokenToCoordinate:
                        tokenToCoordinate[token] = []
                    tokenToCoordinate[token].append(label)
    
    db_name = "Temp_Analysis"
    db = client[db_name]
    collectionName = "TokenToCoordinates_Combined3Div"
    db[collectionName].drop()
    
    infoToWrite = []
    import numpy as np
    for token in tokenToCoordinate:
        d = {}
        d["_id"] = token
        d["coordinates"] = tokenToCoordinate[token]
        infoToWrite.append(d)
            
        if len(infoToWrite) > 1000:
            try:
                db[collectionName].insert_many(infoToWrite, ordered=False)
                infoToWrite = []
                print("Performed write")
            except:
                print("Error when doing bulk write")

    if len(infoToWrite) > 0:
        try:
            db[collectionName].insert_many(infoToWrite, ordered=False)
            infoToWrite = []
            print("Performed write")
        except:
            print("Error when doing bulk write")

def formCSVFromGeoInMessages(outputDir, portInput):
    from MongoDBInterface import getMongoClient
    client = getMongoClient(portInput)
    db_name = "Temp_Analysis"
    db = client[db_name]
    
    collectionName = "TokenToCoordinates_Combined3Div"
    from MongoDBInterface import getMongoClient
    client = getMongoClient(portInput)
    db = client[db_name]
    collectionToRead = db[collectionName]
    query = {}
    tweetCursor = collectionToRead.find(query, no_cursor_timeout=True)
    
    rows = [['id', "label", "Americas", "Africa_Europe", "Asia_Australia", "ratioAmericas", "ratioAfrica_Europe", "ratioAsia_Australia", "ratioMax", "total"]]
    import numpy as np
    for userInfo in tweetCursor:
        values = userInfo['coordinates']
        l1 = 0
        l2 = 0
        l3 = 0
        for value in values:
            if value < 0:
                l1 += 1
            elif value == 0:
                l2 += 1
            else:
                l3 += 1
                
        Americas = l1
        Africa_Europe = l2
        Asia_Australia = l3
        ratioAmericas = float(Americas)/float(len(values))
        ratioAfrica_Europe = float(Africa_Europe)/float(len(values))
        ratioAsia_Australia = float(Asia_Australia)/float(len(values))
        ratioMax = np.max([ratioAmericas, ratioAfrica_Europe, ratioAsia_Australia])
        label = None
        if ratioAmericas == ratioMax:
            label = "Americas"
        elif ratioAfrica_Europe == ratioMax:
            label = "Africa_Europe"
        else:
            label = "Asia_Australia"
        #token = userInfo['_id'].encode("utf-8")
        #if token.startswith('@') or token.startswith('#'):
        rows.append([userInfo['_id'].encode("utf-8"), label, Americas, Africa_Europe, Asia_Australia, ratioAmericas, ratioAfrica_Europe, ratioAsia_Australia, ratioMax, len(values)])
        
    fileToStoreTo = outputDir+"combineDBsCoordinateGroundTruthDiv3.csv"
    from Step2ProcessTableOfTweets import writeRowsToCSV
    writeRowsToCSV(rows, fileToStoreTo)
