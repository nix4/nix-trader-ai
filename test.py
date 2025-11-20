import requests

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=GBPUSD&apikey=8IKN1611HYML3IJJ'
r = requests.get(url)
data = r.json()

print(data)

top_gainers_losers = 'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=8IKN1611HYML3IJJ'
r = requests.get(top_gainers_losers)
data = r.json()

print(data)

most_actively_traded = 'https://www.alphavantage.co/query?function=MOST_ACTIVELY_TRADED&apikey=8IKN1611HYML3IJJ'
r = requests.get(most_actively_traded)
data = r.json()

print(data)