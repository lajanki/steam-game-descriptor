# steam-game-descriptor

A Flask based webapp for generating random game descriptions modeled after Steam store. 

## About
A [Markov Chain](https://en.wikipedia.org/wiki/Markov_chain) based text generator trained on a random sample of [Steam store](https://store.steampowered.com/) game descriptions.

In short, a Markov model based text generator splits the training data as ngrams and generates a sequence of words such that every consecutive of _n_ words generated exists somewhere in the training data. In Python terms, the model is a simple dictionary mapping _n-1_ consecutive words to a list of their successors. 

The application consists of three parts:
 1. **parsing for training data**  
    The official [Steamworks API](https://partner.steamgames.com/doc/webapi/ISteamApps) does not support fetching actual application descriptions. Instead the undocumented API [store.steampowered.com/api](https://store.steampowered.com/api) is used (see also the community Wiki: [https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI](https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI))

    This API is rate limited to 200 requests per 5 minute window(?) and when it comes to descriptions only supports making single requests at a time. To work wihtin these limits, only a small sample of all available Steam apps is used in the training and that sample is slowly fetched via multiple requests.

 1. **training the model**  
    Model training is a simple matter of mapping every sequence of _n-1_ words to their successors. The model is serialized to a Google Cloud Storage bucket for later usage and retrained regularly.

 1. **text generation**  
    The user facing side of the webapp. This involves fetching the model and querying it for a sequence of words:

![Webapp flows](./overview.drawio.png)

 
Hosted on Google App Engine.


## Running locally
Install Python packages with  
```
pip install -r requirements.txt
```  
Then, run in localhost with
```
python main.py
```

## Unit tests
Unit tests can be run from the root folder with
```
pytest
```

## Deploy to Google App Engine
To deploy as an App Engine service, install the [gcloud CLI tool](https://cloud.google.com/sdk/gcloud) and run
```
gcloud app deploy
```
This does not deploy scheduling from `cron.yaml`. To do that, run
```
gcloud app deploy cron.yaml
```
Note that scheduling is App Engine specific and will overwerite any existing scheduling.
