import os
import time
import threading
import json
import requests
import uvicorn
import asyncio

from fastapi import FastAPI
from pprint import pprint
from modules import generator

# Define API
API_HOST,API_PORT='0.0.0.0',5000
app = FastAPI()

# Define working directory
workspace = os.path.dirname(os.path.realpath(__file__))


conf = generator.load_conf()

def check_proxy_list(proxy_list):
    if len(proxy_list) == 0: return []

    if conf['check_google']: visit_url = 'https://google.com/'
    else: visit_url = 'https://icanhazip.com/'

    new_proxy_list = proxy_list.copy()

    for proxy in proxy_list:
        try:
            response = requests.request('get', visit_url, proxies={'https':f"{proxy['ip_address']}:{proxy['port']}"}, timeout=conf['timeout'])
        except:
            new_proxy_list.remove(proxy)
            continue
    
    return new_proxy_list
        

class ProxyThreading(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=60):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.proxy_list = self.read_proxy_file() # get previous session proxy list

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def save_proxy_list(self):
        output_dir = os.path.join(workspace, 'output')
        if not os.path.exists(output_dir): os.makedirs(output_dir)

        output_path = os.path.join(output_dir, 'proxy_list.json')

        with open(output_path, 'w') as f:
            json.dump(self.proxy_list, f, indent=4)
        
        return output_path
    
    def read_proxy_file(self):
        proxy_list = []

        output_dir = os.path.join(workspace, 'output')
        if not os.path.exists(output_dir): return []

        output_path = os.path.join(output_dir, 'proxy_list.json')
        if not os.path.exists(output_path): return []

        with open(output_path, 'r') as f:
            try: proxy_list = json.load(f)
            except: pass

        return proxy_list

    def run(self):
        """ Method that runs forever """
        while True:
            # Remove dead proxies
            new_proxy_list = check_proxy_list(self.proxy_list)

            # Add old working proxies to new list
            if (len(new_proxy_list) > 0):
                print(f'\nFound {len(new_proxy_list)} old working proxies, reusing them...')
                self.proxy_list = generator.main(new_proxy_list) 
            else:
                self.proxy_list = generator.main()

            print("Waiting {} seconds before next generation...".format(self.interval))
            time.sleep(self.interval)
    
    def get_proxy_list(self):
        return self.proxy_list


proxyList = ProxyThreading(interval=120)

@app.get('/proxy')
def api_status():
    return { 'online': True }

@app.get('/proxy/get_proxy_list')
def get_proxy_list():
   return proxyList.get_proxy_list()

def run_api():
    asyncio.set_event_loop(asyncio.new_event_loop())
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        loop="asyncio"
    )

run_api()