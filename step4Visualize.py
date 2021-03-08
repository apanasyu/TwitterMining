def formWordCloud(idToCount, label, outputDir):
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt 
    
    wordcloud = WordCloud(font_path='Arial-Unicode-Regular.ttf', width = 300, height = 600, 
    background_color ='white', 
    stopwords = None, 
    min_font_size = 10, max_words=50).fit_words(idToCount) 

    # plot the WordCloud image                        
    plt.figure(figsize = (3, 5), facecolor = None)
    plt.title(label, fontsize=12)
    plt.imshow(wordcloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 
    
    pathToSaveTo = outputDir+label+".png"
    plt.savefig(pathToSaveTo, bbox_inches='tight', dpi = 1200)
    plt.show()
    plt.close()

def visualizeTopNPersonTopicInWordCloud(df, N, label, outputDir):        
    tokens = set(list(df["id"]))
    tokenPersonTopic = set([])
    for token in tokens:
        if len(token) > 1:
            if token.startswith('@') or token.startswith('#'):
                tokenPersonTopic.add(token)

    df = df.loc[df['id'].isin(list(tokenPersonTopic))]
    topN = list(df.nlargest(N, 'totalRecords')["id"])
    topNDF = df.loc[df['id'].isin(topN)]
    tokenToCount = dict(zip(list(topNDF["id"]), list(topNDF['totalRecords'])))
    
    formWordCloud(tokenToCount, label, outputDir)

def boxPlotViz(df, N, port):
    tokens = set(list(df["id"]))
    tokenPersonTopic = set([])
    for token in tokens:
        if len(token) > 1:
            if token.startswith('@') or token.startswith('#'):
                tokenPersonTopic.add(token)

    df = df.loc[df['id'].isin(list(tokenPersonTopic))]
    topN = list(df.nlargest(N, 'totalRecords')["id"])
    
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

def singleTokenViz(token, port):
    import matplotlib.pyplot as plt 
    db_name = "Temp_Analysis"
    collectionTimeDistMessage = "TimeDist_Combined"
    collectionTimeDistUser = "TimeDist_Combined_AtUser"
    collectionTimeFeaturesMessage = "TokenTimeFeaturesProcessed"
    collectionTimeFeaturesUser = "TokenTimeFeaturesProcessedUser"

    from MongoDBInterface import getMongoIntoPandas
    df = getMongoIntoPandas(port, db_name, collectionTimeDistMessage, query={"_id":token})
    hours = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    df = df[hours]
    df.plot.box()
    plt.show()