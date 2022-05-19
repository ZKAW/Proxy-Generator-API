import os
import json
import requests

from pathlib import Path
from bs4 import BeautifulSoup as bs

# Define working directory
workspace = os.path.dirname(os.path.realpath(__file__))
workspace = str(Path(workspace).parent)

def p_format(*args):
    ip_address, port, code, country, anonymity, google, https, last_checked = args

    return {
        "ip_address": ip_address,
        "port": port,
        "code": code,
        "country": country,
        "anonymity": anonymity,
        "google": google,
        "https": https,
        "last_checked": last_checked
    }

def load_proxy_providers():
    with open(os.path.join(workspace,"proxy_providers.json"), 'r') as json_data:
        providers = json.load(json_data)
    return providers


proxy_providers = load_proxy_providers()

# Get proxy from table data (<tr> HTML tags)
class TabProxyGetter:
    def __init__(self, provider):
        self.url = provider['url']
        self.method = provider['method']
        self.proxy_list = []

    def generate_list(self):
        """
        This function returns list of proxy_list and returns []
        in case of failure.
        """

        NUMBER_OF_ATTRIBUTES = 8

        try:
            # getting html content of site..
            page = requests.get(self.url, timeout=2)
        except:
            # returns empty [] if unable to get source code of site
            print("\nFailed to get proxy list from provider: " + self.url)
            return []

        if page.status_code != 200:
            print("\nAn error occured while getting proxy list from provider: " + self.url)
            return []

        soup = bs(page.text, 'html.parser')  # creating soup object

        table = soup.find('table')
        tbody = table.tbody if table else None  # contains rows of IPs and Stuff

        if tbody:
            infos = tbody.find_all('tr')
            for info in infos:
                # each info is a tr from tbody of table
                # extracting info from table rows
                proxy_data_temp = [i.text for i in info]
                if len(proxy_data_temp) == NUMBER_OF_ATTRIBUTES:
                    # after all attributes have been retrieved
                    # from a row, it's time to format it properly.
                    try:
                        proxy = p_format(*proxy_data_temp)

                        proxy_item = {
                            "ip_address": proxy['ip_address'],
                            "port": int(proxy['port']),
                            "method": self.method,
                            "code": proxy['code'],
                            "country": proxy['country'],
                            "anonymity": proxy['anonymity']
                        }

                        if (proxy_item not in self.proxy_list): self.proxy_list.append(proxy_item)

                    except:
                        continue

            # Return generated proxy list
            return self.proxy_list
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)


# Get proxy from raw data (ip:port)
class RawProxyGetter:
    def __init__(self, provider):
        self.url = provider['url']
        self.method = provider['method']
        self.proxy_list = []

    def generate_list(self):
        """
        This function returns list of proxy_list and returns []
        in case of failure.
        """

        try:
            # getting html content of site..
            page = requests.get(self.url, timeout=2)
        except:
            # returns empty [] if unable to get source code of site
            print("Failed to get proxy list from provider: " + self.url + "\n")
            return []

        if page.status_code != 200:
            print("An error occured while getting proxy list from provider: " + self.url + "\n")
            return []
        
        raw_proxy_list = page.text.split('\n')
        
        # Convert to (ip:port) format
        for raw_proxy in raw_proxy_list:
            try:

                proxy_item = {
                    "ip_address": raw_proxy.split(':')[0],
                    "port": int(raw_proxy.split(':')[1]),
                    "method": self.method,
                    "code": None,
                    "country": None,
                    "anonymity": None,
                }

                if (proxy_item not in self.proxy_list): self.proxy_list.append(proxy_item)
            except:
                continue
                    
        # Return generated proxy list
        return self.proxy_list
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)


def generate_proxies_table(provider):
    proxy_list = TabProxyGetter(provider=provider)
    proxy_list.generate_list() # start generating proxies
    return proxy_list.get_proxy_list() # return generated proxies

def generate_proxies_raw(provider):
    proxy_list = RawProxyGetter(provider=provider)
    proxy_list.generate_list() # start generating proxies
    return proxy_list.get_proxy_list() # return generated proxies

def main():
    proxy_list = []

    # Generate proxies from proxy providers
    for provider in proxy_providers:
        print(f"Getting proxies from {provider['url']}...")

        if provider['content_type'].lower() == "table":
            proxies = generate_proxies_table(provider)
        elif provider['content_type'].lower() == "raw":
            proxies = generate_proxies_raw(provider)
        else:
            print("Unknown content type: " + provider['content_type'] + "\n")
            continue
        
        print(f"Found {len(proxies)} proxies from {provider['url']}.\n")

        # Add generated proxies to proxy_list
        proxy_list += proxies

    return proxy_list