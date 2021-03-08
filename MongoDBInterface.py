def getMongoClient(portInput=None):
    from pymongo import MongoClient
    host= 'localhost'
    port = 27017
    if portInput != None:
        port = portInput
    client = MongoClient(host, port) #connect to MongoDB server
    
    return client

def getMongoIntoPandas(portInput, database_name, collection_name, query):
    import pandas as pd
    client = getMongoClient(portInput)
    db = client[database_name]
    collection = db[collection_name]
    if query != None:
        data = pd.DataFrame(list(collection.find(query)))
    else:
        data = pd.DataFrame(list(collection.find()))
    
    return data