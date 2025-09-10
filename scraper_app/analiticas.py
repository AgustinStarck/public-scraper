import requests

def google_autocomplete(query):
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",  # También podés usar "chrome"
        "q": query
    }
    res = requests.get(url, params=params)
    return res.json()[1]  # Lista de sugerencias

print(google_autocomplete("inteligencia artificial"))
