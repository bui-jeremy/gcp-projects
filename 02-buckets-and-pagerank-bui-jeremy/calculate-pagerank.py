import numpy as np
from google.cloud import storage

def fetchLinksFromBucket(bucketName, folderName):
    storageClient = storage.Client()
    bucket = storageClient.bucket(bucketName)
    
    files = bucket.list_blobs(prefix=folderName)
    pageLinks = {}
    
    for file in files:
        pageName = file.name.split('/')[-1].split('.')[0]
        pageContent = file.download_as_text().splitlines()
        
        outgoingLinks = []
        for line in pageContent:
            if 'href' in line.lower() and '"' in line:
                targetPage = line.split('"')[1].split('.')[0]
                outgoingLinks.append(targetPage)
        pageLinks[pageName] = outgoingLinks
    
    return pageLinks

def computeLinkStatistics(pageLinks):
    # get counts of outgoing links for each file
    outgoingCounts = []
    incomingCounts = {page: 0 for page in pageLinks} 

    # calculate outgoing links and populate incoming link counts
    for page, links in pageLinks.items():
        outgoingCounts.append(len(links))
        for link in links:
            if link in incomingCounts:
                incomingCounts[link] += 1

    # calculate statistics for outgoing links
    avgOutgoingLinks = np.mean(outgoingCounts) if outgoingCounts else float('nan')
    medianOutgoingLinks = np.median(outgoingCounts) if outgoingCounts else float('nan')
    maxOutgoingLinks = np.max(outgoingCounts) if outgoingCounts else float('nan')
    minOutgoingLinks = np.min(outgoingCounts) if outgoingCounts else float('nan')
    quintilesOutgoing = np.percentile(outgoingCounts, [20, 40, 60, 80]) if outgoingCounts else [float('nan')] * 5
    # calculate statistics for incoming links
    incomingCountsList = list(incomingCounts.values())
    avgIncomingLinks = np.mean(incomingCountsList) if incomingCountsList else float('nan')
    medianIncomingLinks = np.median(incomingCountsList) if incomingCountsList else float('nan')
    maxIncomingLinks = np.max(incomingCountsList) if incomingCountsList else float('nan')
    minIncomingLinks = np.min(incomingCountsList) if incomingCountsList else float('nan')
    quintilesIncoming = np.percentile(incomingCountsList, [20, 40, 60, 80]) if incomingCountsList else [float('nan')] * 5

    # print statistics for outgoing and incoming links
    print("Outgoing Links - average: " + str(avgOutgoingLinks) + ", median: " + str(medianOutgoingLinks) +
          ", max: " + str(maxOutgoingLinks) + ", min: " + str(minOutgoingLinks) + ", quintiles: " + str(quintilesOutgoing))
    print("Incoming Links - average: " + str(avgIncomingLinks) + ", median: " + str(medianIncomingLinks) +
          ", max: " + str(maxIncomingLinks) + ", min: " + str(minIncomingLinks) + ", quintiles: " + str(quintilesIncoming))

    return (avgOutgoingLinks, medianOutgoingLinks, maxOutgoingLinks, minOutgoingLinks, quintilesOutgoing,
            avgIncomingLinks, medianIncomingLinks, maxIncomingLinks, minIncomingLinks, quintilesIncoming)

def calculatePageRank(pageLinks, tolerance=0.005, randomJumpProbability=0.85):
    if len(pageLinks) == 0:
        print("no pages to compute pagerank.")
        return []
    
    pageRank = {}
    for page in pageLinks:
        pageRank[page] = 1 / len(pageLinks)
    
    outgoingCounts = {}
    for page, outgoing in pageLinks.items():
        outgoingCounts[page] = len(outgoing)
    incomingLinks = {}
    for page in pageLinks:
        incomingLinks[page] = []
    for page, outgoing in pageLinks.items():
        for targetPage in outgoing:
            incomingLinks[targetPage].append(page) 
    
    delta = tolerance + 1
    iterationCount = 0
    
    # keep iterating until the change in pagerank values is small enough
    while delta > tolerance:
        iterationCount += 1
        newPageRank = {}
        
        for page in pageLinks:
            newPageRank[page] = (1 - randomJumpProbability) / len(pageLinks)
            
            totalIncomingRank = 0
            for incomingPage in incomingLinks.get(page, []):
                if outgoingCounts[incomingPage] > 0:
                    totalIncomingRank += pageRank[incomingPage] / outgoingCounts[incomingPage]
            newPageRank[page] += randomJumpProbability * totalIncomingRank
        
        # calculate the total change across all pages
        delta = 0
        for page in pageRank:
            delta += abs(newPageRank[page] - pageRank[page])
        pageRank = newPageRank
            
    # sort the pages by pagerank and get the top 5
    pageRankList = [(page, score) for page, score in pageRank.items()]
    pageRankList.sort(key=lambda x: x[1], reverse=True)
    top5Pages = pageRankList[:5]
    
    return top5Pages

def main():
    bucketName = 'jeremybui_ps2'
    folderName = 'files'              
    
    pageLinks = fetchLinksFromBucket(bucketName, folderName)
    
    if not pageLinks:
        print("no links were found.")
        return
    computeLinkStatistics(pageLinks) 
    top5PagesByRank = calculatePageRank(pageLinks)
    if top5PagesByRank:
        print("Top 5 pages by PageRank:")
        for page, score in top5PagesByRank:
            print("page: " + page + ", pagerank: " + str(score))

if __name__ == "__main__":
    main()
