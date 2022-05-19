from pprint import pprint

dictlist1 = [
    {
        "ip_address": "195.201.195.19",
        "port": 52609,
        "code": "DE",
        "country": "Germany",
        "anonymity": "elite proxy",
        "check_google": True,
        "method": "https",
        "last_check": "2022-05-17 14:15:17",
        "ms": 10
    },
    {
        "ip_address": "20.195.107.226",
        "port": 80,
        "code": "SG",
        "country": "Singapore",
        "anonymity": "anonymous",
        "check_google": True,
        "method": "https",
        "last_check": "2022-05-17 14:16:17",
        "ms": 11
    }
]

dictlist2 = [
    {
        "ip_address": "20.195.107.226",
        "port": 80,
        "code": "SG",
        "country": "Singapore",
        "anonymity": "anonymous",
        "check_google": True,
        "method": "https",
        "last_check": "2022-05-17 14:26:17",
        "ms": 21
    },
    {
        "ip_address": "80.80.99.99",
        "port": 80,
        "code": "SG",
        "country": "Singapore",
        "anonymity": "anonymous",
        "check_google": True,
        "method": "https",
        "last_check": "2022-05-17 14:26:17",
        "ms": 22
    }
]


for dictelem1 in dictlist1:
    for dictelem2 in dictlist2:
        if dictelem1['ip_address'] == dictelem2['ip_address']:
            dictelem1.update(dictelem2)

pprint(dictlist1)
print('\n')
pprint(dictlist2)