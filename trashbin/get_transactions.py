import requests
import json

URL = "https://www.csast.csas.cz/webapi/api/v3/netbanking/my/transactions"
token = "3/srEu6I5NpglDal4equfztOrXlRFdjmsCpndRKcEcQRNX1xbzTQ8rAZ0Tc1kRglGn"
api_key = "4b8d5c6b-2101-464b-a987-0571f8ead003"


def clearTransaction(transaction):
  result = {}

  result["id"] = transaction.get("id")
  result["title"] = transaction.get("title")
  result["cardTransaction"] = transaction.get("cardId") != None
  result["receiverIBAN"] = transaction.get("receiver").get("iban")
  result["direction"] = "IN" if transaction.get("txDirection") == "INCOMING" else "OUT"
  result["amount"] = transaction.get("amount").get("value")/10**transaction.get("amount").get("precision")

  return result

def getTransactions(url, token, api_key, page=None):
  result = []
  next_page = None
  if page:
    url = "%s?page=%d" % (url, page)
  req = requests.request("GET", url, headers={"web-api.key": api_key, "Authorization": "Bearer %s" % token})
  data = req.json()

  if data.get("currentPage") < data.get("totalPages", 0)-1:
    next_page = data.get("currentPage", 0)+1

  if data.get("collection"):
    for t in data.get("collection"):
      result.append(clearTransaction(t))

  return result, next_page

page = 0
result = []
while page is not None:
  data, page = getTransactions(URL, token, api_key, page)
  result += data

print(json.dumps(result))