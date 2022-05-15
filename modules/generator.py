import os
import json
import requests
import datetime
import urllib.request

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

def load_conf():
    with open(os.path.join(workspace,"conf.json"), 'r') as json_data:
        conf = json.load(json_data)
    return conf

def load_proxy_providers():
    with open(os.path.join(workspace,"proxy_providers.json"), 'r') as json_data:
        providers = json.load(json_data)
    return providers

conf = load_conf()
proxy_providers = load_proxy_providers()


def check_proxy(proxy, timeout=1, check_google=True):
    if check_google: visit_url = 'https://google.com/'
    else: visit_url = 'https://icanhazip.com/'

    try:
        proxy_handler = urllib.request.ProxyHandler({proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"})        
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req = urllib.request.Request(visit_url)
        sock=urllib.request.urlopen(req, timeout=timeout)
        response = requests.get(visit_url, proxies={proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"}, timeout=timeout)
        ms = int(response.elapsed.total_seconds()*100)
        ms = round(ms, 2)

        return (True, ms)
    except:
        return (False, None)

# Generate proxy from table data (<tr> HTML tags)
class ProxyGenerator:
    def __init__(self, length=10, max_ms=500, timeout=1, check_google=True, url="https://free-proxy-list.net/", methods=["https"]):
        self.length = length
        self.max_ms = max_ms
        self.timeout = timeout
        self.check_google = check_google
        self.url = url
        self.methods = methods
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
                if self.get_proxy_amount() >= self.length: # if we have enough proxies
                    break
                # each info is a tr from tbody of table
                # extracting info from table rows
                proxy_data_temp = [i.text for i in info]
                if len(proxy_data_temp) == NUMBER_OF_ATTRIBUTES:
                    # after all attributes have been retrieved
                    # from a row, it's time to format it properly.
                    try:
                        proxy = p_format(*proxy_data_temp)

                        check = (False, None)
                        for method in self.methods:
                            try:
                                proxy['method'] = method.lower()
                                check = check_proxy(proxy, timeout=self.timeout, check_google=self.check_google)
                                if (check[0] and check[1] != None): break
                            except:
                                status = f"{proxy['ip_address']}:{proxy['port']} ({method}) -> Failed (Unknown Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                                print(status, end='\r')
                                continue

                        if not check[0] or check[1] == None:
                            status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                            print(status, end='\r')
                            continue

                        ms = check[1]
                        if ms > self.max_ms:
                            status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed ({ms}ms but max is {self.max_ms}ms) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                            print(status, end='\r')
                            continue

                        if proxy['https'] == "yes": proxy['https'] = True
                        else: proxy['https'] = False
                        proxy['ms'] = ms

                        proxy_item = {
                            "ip_address": proxy['ip_address'],
                            "port": int(proxy['port']),
                            "code": proxy['code'],
                            "country": proxy['country'],
                            "anonymity": proxy['anonymity'],
                            "check_google": self.check_google,
                            "method": proxy['method'],
                            "last_check": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "ms": proxy['ms']
                        }

                        if (proxy_item not in self.proxy_list): self.proxy_list.append(proxy_item)
                        status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) ({ms}ms) -> Success - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\n')

                    except KeyboardInterrupt:
                        print('\nStopping...')
                        if len(self.proxy_list) <= 1:
                            exit()
                        else:
                            break
                    except:
                        status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Unknown Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue

            # Return generated proxy list
            if len(self.proxy_list) >= 1:
                print(f'\nFinished processing proxy list.')
            else:
                print('\nFinished processing proxy list, but no proxy were found.')

            return self.proxy_list
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)

# Generate proxy from raw data (ip:port)
class RawProxyGenerator:
    def __init__(self, length=10, max_ms=500, timeout=1, check_google=True, url="https://proxy-list.download/api/v1/get?type=https", methods=["https"]):
        self.length = length
        self.max_ms = max_ms
        self.timeout = timeout
        self.check_google = check_google
        self.url = url
        self.methods = methods
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
            print("\nFailed to get proxy list from provider: " + self.url)
            return []

        if page.status_code != 200:
            print("\nAn error occured while getting proxy list from provider: " + self.url)
            return []
        
        raw_proxy_list = page.text.split('\n')
        
        # Convert to (ip:port) format
        for raw_proxy in raw_proxy_list:
            try:
                # try:
                proxy = {
                    "ip_address": raw_proxy.split(':')[0],
                    "port": int(raw_proxy.split(':')[1]),
                }
                # except:
                #     status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Formatting Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                #     print(status, end='\r')
                #     continue
                
                check = (False, None)
                for method in self.methods:
                    try:
                        proxy['method'] = method.lower()
                        check = check_proxy(proxy, timeout=self.timeout, check_google=self.check_google)
                        if (check[0] and check[1] != None): break
                    except:
                        status = f"{proxy['ip_address']}:{proxy['port']} ({method}) -> Failed (Unknown Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue

                if not check[0] or check[1] == None:
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                    print(status, end='\r')
                    continue

                ms = check[1]
                if ms > self.max_ms:
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed ({ms}ms but max is {self.max_ms}ms) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                    print(status, end='\r')
                    continue
                
                proxy['ms'] = ms

                proxy_item = {
                    "ip_address": proxy['ip_address'],
                    "port": int(proxy['port']),
                    "code": 'unknown',
                    "country": 'unknown',
                    "anonymity": 'unknown',
                    "check_google": self.check_google,
                    "method": proxy['method'],
                    "last_check": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ms": proxy['ms']
                }

                if (proxy_item not in self.proxy_list): self.proxy_list.append(proxy_item)
                status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) ({ms}ms) -> Success - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                print(status, end='\n')
            except:
                status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Unknown Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                print(status, end='\r')
                continue
                    
        # Return generated proxy list
        if len(self.proxy_list) >= 1:
            print(f'\nFinished processing proxy list.')
        else:
            print('\nFinished processing proxy list, but no proxy were found.')

        return self.proxy_list
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)


def generate_proxies_table(url, methods, amount):
    proxy_list = ProxyGenerator(amount,
        max_ms=conf['max_ms'],
        timeout=conf['timeout'],
        check_google=conf['check_google'],
        url=url,
        methods=methods
    )
    proxy_list.generate_list() # start generating proxies
    return proxy_list.get_proxy_list() # return generated proxies

def generate_proxies_raw(url, methods, amount):
    proxy_list = RawProxyGenerator(amount,
        max_ms=conf['max_ms'],
        timeout=conf['timeout'],
        check_google=conf['check_google'],
        url=url,
        methods=methods
    )
    proxy_list.generate_list() # start generating proxies
    return proxy_list.get_proxy_list() # return generated proxies

def main(proxy_list = []):
    if len(proxy_list) >= conf['length']: return proxy_list

    # Generate proxies from proxy providers
    for provider in proxy_providers:
        if len(proxy_list) >= conf['length']: break
        print(f"\nGetting proxies from {provider['url']}...")

        if provider['content_type'].lower() == "table":
            proxies = generate_proxies_table(provider['url'], provider['methods'], conf['length'] - len(proxy_list))
        elif provider['content_type'].lower() == "raw":
            proxies = generate_proxies_raw(provider['url'], provider['methods'], conf['length'] - len(proxy_list))
        else:
            print("\nUnknown content type: " + provider['content_type'])
            continue

        # Add generated proxies to proxy_list
        proxy_list += proxies

    return proxy_list