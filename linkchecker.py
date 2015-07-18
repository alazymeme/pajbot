from actions import Action, ActionQueue
from bs4 import BeautifulSoup
from apiwrappers import SafeBrowsingAPI
from tbutil import time_limit

import re
import requests

class LinkChecker:
    def __init__(self, bot):
        if 'safebrowsingapi' in bot.config['main']:
            self.safeBrowsingAPI = SafeBrowsingAPI(bot.config['main']['safebrowsingapi'], bot.nickname, bot.version)
        else:
            self.safeBrowsingAPI = None
        return

    def check_url(self, url, action):
        if self.safeBrowsingAPI:
            if self.safeBrowsingAPI.check_url(url): # harmful url detected
                action.func(*action.args, **action.kwargs) # execute the specified action
                return

        try: r = requests.head(url, allow_redirects=True)
        except: return
        checkcontenttype = ('content-type' in r.headers and r.headers['content-type'] == 'application/octet-stream')
        checkdispotype = ('disposition-type' in r.headers and r.headers['disposition-type'] == 'attachment')

        if checkcontenttype or checkdispotype: # triggering a download not allowed
            action.func(*action.args, **action.kwargs)

        if 'content-type' not in r.headers or not r.headers['content-type'].startswith('text/html'):
            return

        try:
            with time_limit(2):
                r = requests.get(url)
        except: return  
            
        try: soup = BeautifulSoup(r.text, 'html.parser')
        except: return

        urls = []
        for link in soup.find_all('a'): # get a list of links to external sites
            url = link.get('href')
            if url.startswith('http://') or url.startswith('https://'):
                urls.append(url)

        for url in urls: # check if the site links to anything dangerous
            if self.safeBrowsingAPI:
                if self.safeBrowsingAPI.check_url(url): # harmful url detected
                    action.func(*action.args, **action.kwargs) # execute the specified action
                    return           

        #if we got here, the site is clean for our standards            

        return

    def findUrlsInMessage(self, msg_raw):
        regex = r'((http:\/\/)|\b)(\w|\.)*\.(((aero|asia|biz|cat|com|coop|edu|gov|info|int|jobs|mil|mobi|museum|name|net|org|pro|tel|travel|[a-zA-Z]{2})\/\S*)|(aero|asia|biz|cat|com|coop|edu|gov|info|int|jobs|mil|mobi|museum|name|net|org|pro|tel|travel|[a-zA-Z]{2}))'

        _urls = re.finditer(regex, msg_raw)
        urls = []
        for i in _urls:
            url = i.group(0)
            if not (url.startswith('http://') or url.startswith('https://')): url = 'https://' + url             
            urls.append(url)

        return urls
