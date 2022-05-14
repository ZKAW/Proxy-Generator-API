import json
import requests
import datetime

from bs4 import BeautifulSoup as bs


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
    with open("conf.json", 'r') as json_data:
        conf = json.load(json_data)
    return conf


class ProxyGenerator:
    def __init__(self, length=10, max_ms=500, timeout=1, check_google=True, url="https://free-proxy-list.net/"):
        self.length = length
        self.max_ms = max_ms
        self.timeout = timeout
        self.check_google = check_google
        self.url = url
        self.proxy_list = []

    def generate_list(self):
        """
        This function returns list of proxy_list and returns []
        in case of failure.
        """

        # url to check connection using proxy
        if self.check_google: visit_url = 'https://google.com/'
        else: visit_url = 'https://icanhazip.com/' 

        NUMBER_OF_ATTRIBUTES = 8
        request_method = 'get'

        try:
            # getting html content of site..
            page = requests.get(self.url)
        except:
            # returns empty [] if unable to get source code of site
            print("\nFailed to get Proxy List :( \nTry Running the script again..")
            return []

        if page.status_code != 200:
            print("\nSomething went wrong while getting proxy list!\n")
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

                        response = requests.request(request_method, visit_url, proxies={'https':f"{proxy['ip_address']}:{proxy['port']}"}, timeout=self.timeout)

                        ms = int(response.elapsed.total_seconds()*100)
                        ms = round(ms, 2)

                        if ms > self.max_ms:
                            status = f"{proxy['ip_address']}:{proxy['port']} -> Failed ({ms}ms but max is {self.max_ms}ms) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                            print(status, end='\r')
                            continue
                        else:
                            if proxy['https'] == "yes": proxy['https'] = True
                            else: proxy['https'] = False
                            proxy['ms'] = ms

                            proxy_item = {
                                "ip_address": proxy['ip_address'],
                                "port": int(proxy['port']),
                                "code": proxy['code'],
                                "country": proxy['country'],
                                "anonymity": proxy['anonymity'],
                                "check_google": conf['check_google'],
                                "https": proxy['https'],
                                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "ms": proxy['ms']
                            }
                            self.proxy_list.append(proxy_item)
                            status = f"{proxy['ip_address']}:{proxy['port']} ({ms}ms) -> Success - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                            print(status, end='\n')

                    except KeyboardInterrupt:
                        print('\nStopping...')
                        if len(self.proxy_list) <= 1:
                            exit()
                        else:
                            break
      
                    except requests.exceptions.ProxyError:
                        status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Proxy Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue
                    except requests.exceptions.Timeout:
                        status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Timeout) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue
                    except requests.exceptions.ConnectionError:
                        status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Connection Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue
                    except:
                        status = f"{proxy['ip_address']}:{proxy['port']} -> Failed (Unknown Error) - Valid proxies: {self.get_proxy_amount()}/{self.length}" + 10*" "
                        print(status, end='\r')
                        continue

                print(f'Valid proxy: {str(self.get_proxy_amount())}/{str(self.length)}\n')


            # Save results to json file
            if len(self.proxy_list) >= 1:
                print(f'\nFinished processing proxy list.')
            else:
                print('\nFinished processing proxy list, but no proxy were found.')

            return self.proxy_list
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)

conf = load_conf()

def main(proxy_list = []):

    free_proxy = ProxyGenerator(length=conf['length'] - len(proxy_list), # substract old proxies from length
                max_ms=conf['max_ms'],
                timeout=conf['timeout'],
                check_google=conf['check_google'],
                url="https://free-proxy-list.net/"
            )

    free_proxy.generate_list()
    proxy_list += free_proxy.get_proxy_list() # add generated proxies to proxy_list

    if (len(free_proxy.get_proxy_list()) < conf['length']): # if we don't have enough proxies
        print(f'\nNot enough proxies, trying to get more from sslproxies.org...')
        ssl_proxy = ProxyGenerator(length=conf['length'] - len(free_proxy.get_proxy_list()), # substract free_proxy proxies from length
            max_ms=conf['max_ms'],
            timeout=conf['timeout'],
            check_google=conf['check_google'],
            url="https://sslproxies.org/"
        )
        ssl_proxy.generate_list() # generate more
        proxy_list += ssl_proxy.get_proxy_list() # add generated proxies to proxy_list

    return proxy_list

if __name__ == '__main__':
    print('\nStarting...\n')
    print(main())
    print("\nFinished generating proxy list.\n")