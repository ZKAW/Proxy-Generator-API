import urllib
import requests

def check_proxy(proxy, timeout=1, check_google=True):
    if check_google: visit_url = 'https://google.com/'
    else: visit_url = 'https://icanhazip.com/'

    try:
        proxy_handler = urllib.request.ProxyHandler({proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"})        
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req = urllib.request.Request(visit_url)
        urllib.request.urlopen(req, timeout=timeout)
        response = requests.get(visit_url, proxies={proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"}, timeout=timeout)
        ms = int(response.elapsed.total_seconds()*100)
        ms = round(ms, 2)

        return (True, ms)
    except:
        return (False, None)

def check_duplicate(proxy_list, proxy):
    for proxy_check in proxy_list:
        if proxy_check['ip_address'] == proxy['ip_address'] and proxy_check['port'] == proxy['port']:
            return True
    return False