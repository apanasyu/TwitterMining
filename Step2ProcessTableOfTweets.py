def analyzeTokensInTables(db_nameAndCollection, minFreq, outputDir, port):
    tokenToFrequencyGlobal = getTokenToFrequencyGlobal(db_nameAndCollection, outputDir, port)

    setupTempTableWithTimeDistributionforEachToken(db_nameAndCollection, minFreq, port, tokenToFrequencyGlobal)
    processTimeDistributions(minFreq, port, tokenToFrequencyGlobal, outputDir)
    
    setupTempTableWithTimeDistributionforEachToken(db_nameAndCollection, minFreq, port, tokenToFrequencyGlobal, True)
    processTimeDistributions(minFreq, port, tokenToFrequencyGlobal, outputDir, True)
    
def writeRowsToCSV(rows, fileToWriteToCSV):
    import csv
    if len(rows) > 0:
        with open(fileToWriteToCSV, "w") as fp:
            a = csv.writer(fp, delimiter=',')
            a.writerows(rows)
            fp.close()
            print("Written " + str(len(rows)) + " rows to: " + fileToWriteToCSV)

def processTimeDistributions(minFreq, port, tokenToFrequencyGlobal, outputDir, atUser=False):
    tokenOfInterest = set([])
    for token in tokenToFrequencyGlobal:
        if tokenToFrequencyGlobal[token] >= minFreq:
            tokenOfInterest.add(token)

    db_name = "Temp_Analysis"
    collectionName = "TimeDist_Combined"
    if atUser:
        collectionName = "TimeDist_Combined_AtUser"
    
    from MongoDBInterface import getMongoClient
    client = getMongoClient(port)
    db = client[db_name]
    collectionToRead = db[collectionName]
    query = {}
    tweetCursor = collectionToRead.find(query, no_cursor_timeout=True)
    
    collectionNameToWriteTo = "TokenTimeFeaturesProcessed"
    if atUser:
        collectionNameToWriteTo = "TokenTimeFeaturesProcessedUser"
        
    db = client["Temp_Analysis"]
    collectionName = collectionNameToWriteTo
    db[collectionName].drop()
    
    timeOfDay = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    header = timeOfDay+['indexOfMin', "indexOfMax", "stdOfTimeDist", 'rSquare', "power", "predUTC", 'totalRecords', 'id']
    import numpy as np
    infoToWrite = []
    for userInfo in tweetCursor:
        timeDist = userInfo

        idToken = timeDist.pop('_id')
        if idToken in tokenOfInterest:
            if np.min(list(timeDist.values())) > 0:
                values = []
                total = np.sum(list(timeDist.values()))
                for t in timeOfDay:
                    if t in timeDist:
                        values.append(float(timeDist[t])/float(total))
                    else:
                        values.append(0)
                
                stdOfTimeDist = np.std(values)
                
                resultsTemp = processTimeDist(values, 5, 33)
                
                indexOfMax = values.index(np.max(values))
                indexOfMin = values.index(np.min(values))
                
                PSTModified = None
                rSquare = None
                power = None
                if resultsTemp['twoPointTestPass']:
                    if resultsTemp['parabola']:
                        value = resultsTemp['predictedSleepTime']
                        if value >= 14:
                            value = value - 24
                        
                        value = -value + 4
                        PSTModified = value
                        rSquare = resultsTemp['rSquare']
                        power = resultsTemp["power"]
                row  = values + [indexOfMin, indexOfMax, stdOfTimeDist, rSquare, power, PSTModified, total, idToken]
                d = dict(zip(header, row))
                d["_id"] = idToken
                infoToWrite.append(d)
                 
                if len(infoToWrite) > 1000:
                    try:
                        db[collectionName].insert_many(infoToWrite, ordered=False)
                        infoToWrite = []
                        print("Performed write")
                    except:
                        print("Error when doing bulk write")
            
def setupTempTableWithTimeDistributionforEachToken(db_nameAndCollection, minFreq, port, tokenToFrequencyGlobal, atUser=False):
    print("creating time distribution for each token")
    
    field = 'tHour'
    if atUser:
        field = 'tHour2'
    collectionNameToWriteTo = "TimeDist_Combined"
    if atUser:
        collectionNameToWriteTo = "TimeDist_Combined_AtUser"
    
    tokenOfInterest = set([])
    for token in tokenToFrequencyGlobal:
        if tokenToFrequencyGlobal[token] >= minFreq:
            tokenOfInterest.add(token)
    print(str(len(tokenOfInterest)) + " tokenOfInterest")
    
    tokenToTimeDist = {}
    blankTimeDist = {}
    for hour in range(0,24,1):
        blankTimeDist[str(hour)] = 0
    import copy
    usersProcessed = set([])
    for pair in db_nameAndCollection:
        db_name = pair[0]
        collectionName = pair[1]
        
        from MongoDBInterface import getMongoClient
        client = getMongoClient(port)
        db = client[db_name]
        
        collectionToRead = db[collectionName]
        query = {}
        fields = {'tweetOriginal':1, field:1}
        if atUser:
            fields = {'tweetOriginal':1, field:1, 'username':1}
        tweetCursor = collectionToRead.find(query, fields, no_cursor_timeout=True)
        
        if atUser:
            for userInfo in tweetCursor:
                if not userInfo["username"] in usersProcessed:
                    usersProcessed.add(userInfo["username"])
                    tokens = processString(userInfo["tweetOriginal"])
                    for token in tokens:
                        if token in tokenOfInterest:
                            if not token in tokenToTimeDist:
                                tokenToTimeDist[token] = copy.copy(blankTimeDist)
                            tokenToTimeDist[token][str(userInfo[field])] += 1
        else:
            for userInfo in tweetCursor:
                tokens = processString(userInfo["tweetOriginal"])
                for token in tokens:
                    if token in tokenOfInterest:
                        if not token in tokenToTimeDist:
                            tokenToTimeDist[token] = copy.copy(blankTimeDist)
                        tokenToTimeDist[token][str(userInfo[field])] += 1
        
    db = client["Temp_Analysis"]
    collectionName = collectionNameToWriteTo
    db[collectionName].drop()
    
    infoToWrite = []
    import numpy as np
    for token in tokenToTimeDist:
        d = tokenToTimeDist[token]
        d["_id"] = token
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
    
    print("finished creating time distribution for each token")
    
def getTokenToFrequencyGlobal(db_nameAndCollection, outputDir, port):   
    tokenToFrequencyGlobal = {}
    for pair in db_nameAndCollection:
        db_name = pair[0]
        collectionName = pair[1]
        tokenToFrequency = generateFrequencyOfTokens(db_name, collectionName,outputDir, port)
        for token in tokenToFrequency:
            if token in tokenToFrequencyGlobal:
                tokenToFrequencyGlobal[token] += tokenToFrequency[token]
            else:
                tokenToFrequencyGlobal[token] = tokenToFrequency[token]
    
    return tokenToFrequencyGlobal

def generateFrequencyOfTokens(db_name, collectionName, outputDir, port):
    from MongoDBInterface import getMongoClient
    client = getMongoClient(port)
    db = client[db_name]
    
    import os
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)

    fileToStoreTo = outputDir+"tokenToFrequency_"+str(db_name)+"_"+str(collectionName)+".pickle"
    if not os.path.isfile(fileToStoreTo):   
        collectionToRead = db[collectionName]
        query = {}
        fields = {'tweetOriginal':1}
        tweetCursor = collectionToRead.find(query, fields, no_cursor_timeout=True)
        
        tokenToFrequency = {}
        for userInfo in tweetCursor:
            tokens = processString(userInfo["tweetOriginal"])
            for token in tokens:
                if not token in tokenToFrequency:
                    tokenToFrequency[token] = 0
                tokenToFrequency[token] += 1

        import pickle
        with open(fileToStoreTo, "wb") as fp:
            pickle.dump(tokenToFrequency, fp)
    else:
        import pickle
        with open(fileToStoreTo, "rb") as fp:
            tokenToFrequency = pickle.load(fp)
    
    print("loaded " + str(len(tokenToFrequency)) + " tokens.")
    
    return tokenToFrequency

def processString(stringToProcess):
    import re
    from nltk.tokenize import word_tokenize
    from nltk.tokenize import TweetTokenizer
    w_tokenizer = TweetTokenizer()
    stringToProcess = re.sub(r"http\S+", "", stringToProcess)
    tokens = w_tokenizer.tokenize(stringToProcess.lower())

    return tokens

def processTimeDist(values, nToUse, percentileToUse):
    result = {}
    import numpy as np
    import math
    totalRecords = np.sum(values)
    valuesNormalized = []
    for value in values:
        normalizedValue = float(value)/float(totalRecords)
        valuesNormalized.append(normalizedValue)
    
    import copy
    y24 = copy.copy(valuesNormalized)
    y48 = y24+y24
    
    n = nToUse
    nToDist = {}
    hourToValue = {}
    minSumAcrossN = {"sum":[],"i":[]}
    for i in range(0,len(y24),1):
        minSumAcrossN["sum"].append(np.sum(y48[i:i+n]))
        indexToRecord = i+(n-1)/2
        if indexToRecord >= 24:
            indexToRecord -= 24
        minSumAcrossN["i"].append(indexToRecord)
        hourToValue[indexToRecord] = np.sum(y48[i:i+n])
        
    totalSum = np.sum(minSumAcrossN["sum"])
    valuesNormalizedEntropySleepCycle = []
    for i in range(0,24,1):
        normalizedValue = float(hourToValue[i])/float(totalSum)
        valuesNormalizedEntropySleepCycle.append(normalizedValue)
    nToDist[n] = valuesNormalizedEntropySleepCycle

    numHours = 48
    x = np.array(range(0,numHours,1))
    f = nToDist[n]
    g = [np.percentile(f, percentileToUse)]*24
    f += f
    g += g
    
    xNew = []
    stepsPer1 = 10
    stepSize = float(1)/float(stepsPer1)
    xValue = 0
    for i in range(0,numHours,1):
        for j in range(0,stepsPer1,1):
            xNew.append(xValue)
            xValue += stepSize
    fNew = np.interp(xNew, x, f)
    gNew = np.interp(xNew, x, g)
    
    x = np.array(xNew)
    f = np.array(fNew)
    g = np.array(gNew)

    idx = np.argwhere(np.diff(np.sign(f - g))).flatten()
    twoPointTestPass = False
    if numHours == 48:
        if len(idx) >= 3 and len(idx) <= 4:
            twoPointTestPass = True
    result["twoPointTestPass"] = twoPointTestPass
    result["twoPointTestNumPoints"] = len(idx)
    
    xStart = None
    xEnd = None
    if twoPointTestPass:
        if numHours == 48:
            for i in idx:
                a1 = np.interp(x[i]-0.5, x, f)
                a2 = np.interp(x[i]+0.5, x, f)
                sign = ""
                if a1<a2:
                    sign = "-to+"
                elif a1>a2:
                    sign = "+to-"
                else:
                    import matplotlib.pyplot as plt2
                    line2d = plt2.plot(x, f, '-')
                    xvalues = line2d[0].get_xdata()
                    yvalues = line2d[0].get_ydata()
                    plt2.plot(x, g, '-')
                    plt2.plot(x[idx], g[idx], 'ro')
                if xStart == None or xEnd == None:
                    if sign == "+to-" and xStart == None:
                        xStart = x[i]
                    elif sign == "-to+" and xStart != None and xEnd == None:
                        xEnd = x[i]
        
        parabola = False
        if xStart != None and xEnd != None:
            rangeInSleepCycle = xEnd-xStart
            xStartIndex = list(x).index(xStart)
            xEndIndex = list(x).index(xEnd)
            xToFit = list(x)[xStartIndex:xEndIndex+1]
            yToFit = list(f)[xStartIndex:xEndIndex+1]
            
            xd = xToFit
            yd = yToFit
            order = 2
            coeffs = np.polyfit(xd, yd, order)
            c = np.poly1d(coeffs)
            crit = c.deriv().r
            r_crit = crit[crit.imag==0].real
            test = c.deriv(2)(r_crit) 
            x_min = r_crit[test>0]
            y_min = c(x_min)
            y_atX0 = c(np.min(xd))
            y_atXN = c(np.max(xd))
            
            #check if function is a parabola
            parabola = False
            predictedSleepTime = -1
            if len(x_min) == 1:
                x_min = x_min[0]
                y_min = y_min[0]
                
                if y_atX0 > y_min and y_atXN > y_min:
                    parabola = True
            
        if parabola: 
            predictedSleepTime = x_min
            if predictedSleepTime >= 24:
                predictedSleepTime -= 24
            
            #Calculate R Squared
            p = np.poly1d(coeffs)
            ybar = np.sum(yd) / len(yd)
            ssreg = np.sum((p(xd) - ybar) ** 2)
            sstot = np.sum((yd - ybar) ** 2)
            Rsqr = ssreg / sstot
            
            result["power"] = coeffs[0]
            result["slope"] = coeffs[1]
            result["intercept"] = coeffs[2]
            result["rSquare"] = Rsqr
            result["predictedSleepTime"] = predictedSleepTime
            result["parabola"] = parabola
        else:
            result["parabola"] = parabola
    
    return result