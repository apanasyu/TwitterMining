if __name__ == '__main__':
    pass

    outputDir = "programOutput/"
    import os
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)

    step1 = False
    step2 = False
    step3 = False
    step3B = True
    port = 27020
    db_name = "RawTweetCollection"
    if step1:
        '''
        this will keep writing a stream of tweets to a new MongoDB table every 24 hours
        code will keep executing until terminated by the user  
        '''
        from Step1CollectAStreamOfTweets import performRawCollection
        performRawCollection(db_name, port)
    
    if step2:
        '''
        Execute once 24 hour of tweets have finished writing to Table in MongoDB
        multiple collections can be analyzed, for example:
        db_nameAndCollection = [["RawTweetCollection", "Day1"], ["RawTweetCollection", "Day2"]]
        
        Program will result in additional MongoDB:
        db_name = "Temp_Analysis"
        a. collectionTimeDistMessage = "TimeDist_Combined"
        b. collectionTimeDistUser = "TimeDist_Combined_AtUser"
        c. collectionTimeFeaturesMessage = "TokenTimeFeaturesProcessed"
        d. collectionTimeFeaturesUser = "TokenTimeFeaturesProcessedUser"
        
        a and b hold time distributions
        c and d hold features over time distributions such as UTC prediction
        
        Table created using message creation times or user creation times (as specified in name of table)
        '''
        
        db_nameAndCollection = [["RawTweetCollection", "Day1"]]
        minFreq = 500
        from Step2ProcessTableOfTweets import analyzeTokensInTables
        analyzeTokensInTables(db_nameAndCollection, minFreq, outputDir, port)
    
    if step3:
        '''
        form regions using temporal features and generate WordCloud
        tables from step2 are returned as Pandas DataFrames
        '''

        from Step3AnalyzeTokens import getTokenToRegion
        rSquareT = 0.85
        minRecordT = 500
        powerC2T = 0.001
        atUser = False
        americas, africaEurope, asiaAustralia = getTokenToRegion(port, atUser, rSquareT, minRecordT, powerC2T)
    
        N = 50
        from step4Visualize import visualizeTopNPersonTopicInWordCloud
        visualizeTopNPersonTopicInWordCloud(americas, N, "Americas_WordCloud", outputDir)
        visualizeTopNPersonTopicInWordCloud(africaEurope, N, "AfricaEurope_WordCloud", outputDir)
        visualizeTopNPersonTopicInWordCloud(asiaAustralia, N, "Asia_Oceania_WordCloud", outputDir)
    
        '''
        example of other visualizations
        '''
        #from step4Visualize import boxPlotViz
        #boxPlotViz(asiaAustralia, N, port)
        #from step4Visualize import singleTokenViz
        #singleTokenViz('@blackpink', port)
    
    if step3B:
        '''
        form regions using geo in messages as an additional evaluation
        against tokens assigned based on temporal regions
        '''
        db_nameAndCollection = [["RawTweetCollection", "Day1"]]
        from Step3BAssignLabelUsingGeo import tokenToCoordinates3Div
        from Step3BAssignLabelUsingGeo import formCSVFromGeoInMessages
        tokenToCoordinates3Div(db_nameAndCollection, port)
        formCSVFromGeoInMessages(outputDir, port)