db_name = "Temp_Analysis"
collectionTimeDistMessage = "TimeDist_Combined"
collectionTimeDistUser = "TimeDist_Combined_AtUser"
collectionTimeFeaturesMessage = "TokenTimeFeaturesProcessed"
collectionTimeFeaturesUser = "TokenTimeFeaturesProcessedUser"
def getTokenToRegion(portInput, atUser, rSquareT=0.85, minRecordT=500, powerC2T=0.001):
    import pandas as pd
    from MongoDBInterface import getMongoIntoPandas
    
    if atUser:
        df = getMongoIntoPandas(portInput, db_name, collectionTimeFeaturesMessage, None)
    else:
        df = getMongoIntoPandas(portInput, db_name, collectionTimeFeaturesUser, None)

    df = df.loc[(df['totalRecords'] >= minRecordT)]
    print(str(len(df)) + " total records with above frequency " + str(minRecordT))
    df = df.loc[(df['rSquare'] >= rSquareT)]
    print(str(len(df)) + " total records with above rSquare " + str(rSquareT))
    df = df.loc[(df['power'] >= powerC2T)]
    print(str(len(df)) + " total records with above power " + str(powerC2T))

    df1 = df.loc[(df['predUTC'] <= -2)]
    americas = set(list(df1["id"]))
    df2 = df.loc[(df['predUTC'] > -2)]
    df2 = df2.loc[(df2['predUTC'] <= 4)]
    africaEurope = set(list(df2["id"]))        
    df3 = df.loc[(df['predUTC'] > 4)]
    asiaAustralia = set(list(df3["id"]))
    
    return df1, df2, df3