#!/usr/bin/env/python3

import json
import requests

data = requests.get("http://api.nobelprize.org/v1/laureate.json").json()
for i in data['laureates']:
    # Only check the first prize (works for Curie)
    if(i['prizes'][0]['category'] == 'physics'):
        print(i['surname'])
