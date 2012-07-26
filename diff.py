import pprint 

import localclient

URL = 'http://localhost:8000/v0.1/site/1/item/listing?lgcy_country=30&lgcy_category=378&limit=1&offset=0'
URL = 'http://dev-models.olx.com.ar:80/v0.1/site/1/item/listing?lgcy_country=30&lgcy_category=378&limit=3&offset=0'


c = localclient.SimpleLocalClient()
d = c.fetch_listing(URL)
d = c.fetch_listing(URL)
with open('full.txt', 'w') as f:
    f.write(pprint.pformat(d))
print c.status()
del(c)

c = localclient.MultiRequestClient()
d = c.fetch_listing(URL)
d = c.fetch_listing(URL)
with open('multi.txt', 'w') as f:
    f.write(pprint.pformat(d))
print c.status()
del(c)

