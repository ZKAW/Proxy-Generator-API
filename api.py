import os
import time
import threading
import urllib
import requests
import json
import uvicorn
import asyncio

from fastapi import FastAPI
from modules import generator

# Define API
API_HOST,API_PORT='0.0.0.0',5000
app = FastAPI()

# Define working directory
workspace = os.path.dirname(os.path.realpath(__file__))

conf = generator.load_conf()
        

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

    def remove_dead_proxy(self):
        if (len(self.proxy_list) == 0): return []

        if conf['check_google']: visit_url = 'https://google.com/'
        else: visit_url = 'https://icanhazip.com/'

        old_proxy_list = self.proxy_list.copy()

        for proxy in old_proxy_list:
            try:
                # Check if proxy is working
                proxy_handler = urllib.request.ProxyHandler({proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"})        
                opener = urllib.request.build_opener(proxy_handler)
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                req = urllib.request.Request(visit_url)
                sock=urllib.request.urlopen(req, timeout=conf['timeout'])
                response = requests.get(visit_url, proxies={proxy['method']: f"{proxy['ip_address']}:{proxy['port']}"}, timeout=conf['timeout'])
                ms = int(response.elapsed.total_seconds()*100)
                ms = round(ms, 2)

                # If response time is too slow, remove proxy
                if (ms > conf['max_ms']):
                    # print(f"Removing {proxy['ip_address']}:{proxy['port']} from proxy list, response time is {ms}ms")
                    self.proxy_list.remove(proxy)
                    continue

                self.proxy_list[self.proxy_list.index(proxy)]['ms'] = ms

            except:
                # print('\nProxy {} is dead, removing...'.format(proxy['ip_address']))
                self.proxy_list.remove(proxy)
                continue
        
        return self.proxy_list

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
    
    def delete_proxy_list(self):
        output_dir = os.path.join(workspace, 'output')
        if not os.path.exists(output_dir): return

        output_path = os.path.join(output_dir, 'proxy_list.json')
        if not os.path.exists(output_path): return

        os.remove(output_path)
        self.proxy_list = []

        return True

    def run(self):
        """ Method that runs forever """
        
        self.remove_dead_proxy()
        if (len(self.proxy_list) > 0): print(f"Proxy list loaded: {len(self.proxy_list)} working proxies")

        while True:
            # Remove dead proxies
            self.remove_dead_proxy()

            if (len(self.proxy_list) >= conf['length']): # already have enough proxies
                print(f"\nProxy list is full, {len(self.proxy_list)}/{conf['length']} proxies")
            elif (len(self.proxy_list) > 0): # Add old working proxies to new list
                print(f'\nFound {len(self.proxy_list)} old working proxies, reusing them...')
                self.proxy_list = generator.main(self.proxy_list) 
            else:
                self.proxy_list = generator.main()

            # Save proxy list for next session
            if (self.read_proxy_file() != self.proxy_list): self.save_proxy_list()

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

@app.get('/proxy/delete_proxy_list')
def delete_proxy_list():
    proxyList.delete_proxy_list()
    return { 'status': 'success' }

def run_api():
    asyncio.set_event_loop(asyncio.new_event_loop())
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        loop="asyncio"
    )

run_api()