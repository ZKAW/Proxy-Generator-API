import os
import sys
import time
import threading
import datetime
import json
import uvicorn
import asyncio

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from helpers import config
from helpers import checker
from workers import generator

# Define API
API_HOST,API_PORT='0.0.0.0',5000
app = FastAPI()

# Define working directory
workspace = os.path.dirname(os.path.realpath(__file__))

# Load config
config = config.load_config()

# better print end='\r'
class OverwriteLast:
    """
    Avoid trailing characters on new line after same line print
    """
    def __init__(self):
        self.last_len = 0
    def print(self, content, end='\r'):

        if len(content) < self.last_len:
            print(content + ' '*(self.last_len-len(content)), end=end)
        else:
            print(content, end=end)

        self.last_len = len(content)


one_line = OverwriteLast()
print_r = one_line.print

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
        self.paused = False
        self.interval = interval
        self.proxy_list = self.read_proxy_file() # get previous session proxy list

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def remove_dead_proxy(self):
        if (self.get_proxy_amount() == 0): return []

        old_proxy_list = self.proxy_list.copy()

        for proxy in old_proxy_list:
            # Check if proxy is working
            check = checker.check_proxy(proxy, timeout=config['timeout'], check_google=config['check_google'])
            if (not check[0]):
                self.proxy_list.remove(proxy)
                continue

            ms = check[1]
            # If response time is too slow, remove proxy
            if (ms > config['max_ms']):
                # print(f"Removing {proxy['ip_address']}:{proxy['port']} from proxy list, response time is {ms}ms")
                self.proxy_list.remove(proxy)
                continue

            # Upgrade proxy values
            self.proxy_list[self.proxy_list.index(proxy)]['ms'] = ms
            self.proxy_list[self.proxy_list.index(proxy)]['last_check'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.proxy_list[self.proxy_list.index(proxy)]['check_google'] = config['check_google']

        
        return self.proxy_list
    
    def check_proxy_list(self, unchecked_proxy_list):
        if len(unchecked_proxy_list) == 0: return []
        new_proxies_counter = 0
        tested_proxies_counter = 0

        for proxy in unchecked_proxy_list:
            tested_proxies_counter += 1

            """ Check if proxy is working """
            check = checker.check_proxy(proxy, timeout=config['timeout'], check_google=config['check_google'])
            if (not check[0]):
                # Remove proxy if already in list
                proxy_check = checker.check_duplicate(self.proxy_list, proxy)
                if (proxy_check):
                    self.proxy_list.remove(proxy_check)
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Removed - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)"
                else:
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)"

                print_r(status)
                continue

            """ Check if response time is too slow """
            ms = check[1]
            if (ms > config['max_ms']): 
                # Remove proxy if already in list
                proxy_check = checker.check_duplicate(self.proxy_list, proxy)
                if (proxy_check):
                    self.proxy_list.remove(proxy_check)
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Removed - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)"
                else:
                    status = f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Failed - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)"

                print_r(status)
                continue

            # Check if proxy is already in proxy list
            proxy_check = checker.check_duplicate(self.proxy_list, proxy)
            if (proxy_check):
                # Update proxy data if proxy is already in list
                self.proxy_list[self.proxy_list.index(proxy_check)]['ms'] = ms
                self.proxy_list[self.proxy_list.index(proxy_check)]['last_check'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.proxy_list[self.proxy_list.index(proxy_check)]['check_google'] = config['check_google']

                print_r(f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Updated - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)", end='\n')
                continue

            # Update proxy values
            proxy['ms'] = ms
            proxy['last_check'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            proxy['check_google'] = config['check_google']
            
            # Add new proxy to proxy list
            self.proxy_list.append(proxy)
            new_proxies_counter += 1
    
            print_r(f"{proxy['ip_address']}:{proxy['port']} ({proxy['method']}) -> Added - Valid proxies: {self.get_proxy_amount()}/{config['amount']} ({len(unchecked_proxy_list) - tested_proxies_counter} remaining)", end='\n')

            # We have enough proxies
            if (self.get_proxy_amount() >= config['amount']): break

        return (self.proxy_list, new_proxies_counter)


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
    
    def convert_seconds_to_time_str(self, seconds):
        seconds = int(seconds)
        if (seconds < 1): return '0s'

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 3600) % 60

        hours_str = str(hours) + "h " if hours > 0 else ""
        minutes_str = str(minutes) + "m " if minutes > 0 else ""
        seconds_str = str(seconds) + "s" if seconds > 0 else ""

        time_str = hours_str + minutes_str + seconds_str
        return time_str.rstrip()

    def run(self):
        """ Method that runs forever """
        
        if (self.get_proxy_amount() > 0): print(f"Loaded {self.get_proxy_amount()} proxies from previous session")

        while True:
            # Check proxy list validity (if not empty)
            if (len(self.proxy_list) > 0): self.check_proxy_list(self.proxy_list)

            # Check if we have enough proxies
            if (self.get_proxy_amount() >= config['amount']): # already have enough proxies
                print(f"\nProxy list is full, {self.get_proxy_amount()}/{config['amount']} proxies")
            else:
                # Generate more proxies
                unchecked_proxy_list = generator.main()
                unchecked_proxy_list = self.proxy_list + unchecked_proxy_list

                # Check new proxy list
                print(f"-> {len(unchecked_proxy_list)} proxies to check\n")
                new_proxies_counter = self.check_proxy_list(unchecked_proxy_list)[1]

                print(f"\n\nFound {new_proxies_counter} new working proxies" + 10*' ')
                print(f"Total valid proxies: {self.get_proxy_amount()}/{config['amount']}\n")

            # Save proxy list for next session
            if (self.read_proxy_file() != self.proxy_list): self.save_proxy_list()

            # Wait before next check
            if (self.interval > 0):
                n = 0
                self.paused = True
                while (n < self.interval) and self.paused:
                    time.sleep(1)
                    n += 1
                    print(f"Waiting {self.convert_seconds_to_time_str(self.interval - n)} before next generation", end='\r')
                self.paused = False
    
    def get_proxy_list(self):
        return self.proxy_list
    
    def get_proxy_amount(self):
        return len(self.proxy_list)

proxyList = ProxyThreading(interval=config['fetch_interval'])

@app.get('/')
def help_page():
    html_content = """
    <h1>Proxy Checker</h1>
    <p>
        <a href="/api/proxy_list" target="_blank">/api/proxy_list</a> - Get proxy list<br>
        <a href="/api/proxy_amount" target="_blank">/api/proxy_amount</a> - Get proxy amount<br>
        <a href="/api/proxy_update" target="_blank">/api/proxy_update</a> - Update proxy list<br>

        <br>
        <a href="/api/proxy_delete" target="_blank">/api/proxy_delete</a> - Delete proxy list
    </p>
    """

    return HTMLResponse(content=html_content, status_code=200)

@app.get('/api')
def api_status():
    return { 'online': True }

@app.get('/api/proxy_list')
def get_proxy_list():
   return proxyList.get_proxy_list()

@app.get('/api/proxy_amount')
def get_proxy_amount():
    amount = proxyList.get_proxy_amount()
    return { 'amount': amount }

@app.get('/api/proxy_update')
def update_proxy_list():
    proxyList.paused = False
    return { 'success': True }

@app.get('/api/proxy_delete')
def delete_proxy_list():
    proxyList.delete_proxy_list()
    return { 'success': True }

def run_api():
    asyncio.set_event_loop(asyncio.new_event_loop())
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        loop="asyncio"
    )

if __name__ == '__main__':
    run_api()