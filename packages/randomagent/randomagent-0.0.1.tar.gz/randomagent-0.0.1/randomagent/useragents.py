import requests
import random

class Useragents:
    def __init__(self, url=None, vb=0):
        self.vb=vb
        import requests
        import random
        try:
            from bs4 import BeautifulSoup
            self.BeautifulSoup=BeautifulSoup
            self.soup=True
        except:
            if self.vb:
                print('beautifulsoup not available, using html parser')
            self.soup=False
        self.useragents=[]
        if not url:
            url='https://www.useragents.me/'
        self.url=url
    def _extract_table(self,table):
        ret=[]
        headers=[]
        for tr in table.find_all('tr'):
            hs=tr.find_all('th')
            if hs:
                headers=[h.text for h in hs]
            else:
                hs=tr.find_all('td')
                entries=[h.text for h in hs]
                ret.append({k:v for k,v in zip(headers, entries)})
        return ret

    def _select_env(self, env=''):
        if not self.useragents:
            self._get_user_agents()
        agents=self.useragents
        if env=='all' or env=='':
            return agents
        f=False
        for k,v in agents.items():
            if env in k.lower():
                agents=v
                f=True
                break
        else:
            if not f:
                if self.vb:
                    print(f'unknown env {env}')
                return []
        return v

    def _get_html(self):
        t=requests.get(self.url)
        if t.status_code!=200:
            if self.vb:
                print('failed to get useragents.me')
            return ''
        return t.text
        
    def _get_user_agents_html_parser(self):
        t=self._get_html()
        parser = H2TableAssociator()
        parser.feed(t)
        tables=parser.tables_with_h2
        def _get_list(ls):
            if not ls:
                return
            hs, es=ls[0], ls[1:]
            return [{h:e for h,e in zip(hs,l)} for l in es]
        def get_agent_dict(tables):
            ret={}
            for h2, table in tables:
                if not h2 in ret:
                    ret[h2]=_get_list(table)    
            return ret
        agents=get_agent_dict(tables)
        if agents:
            self.useragents=agents
            
    def _get_user_agents(self, ):
        if not self.soup:
            self._get_user_agents_html_parser()
            return
        sp=self.BeautifulSoup(self._get_html(), 'html.parser')
        tables=sp.find_all('table')
        agents={}
        for table in tables:
            try:
                title=table.parent.parent.h2.text.strip()
                r=self._extract_table(table)
                if not title in agents:
                    agents[title]=r
            except Exception as e:
                pass
        if agents:
            self.useragents=agents
    
    def get_user_agents(self, env='all'):
        if not self.useragents:
            self._get_user_agents()
        if not self.useragents:
            if self.vb:
                print('failed to get agents')
            return
        agents=self.useragents
        return self._select_env(env)
        
    def get_user_agent(self,env='desktop'):
        if not self.useragents:
            self._get_user_agents()
        agents=self.useragents
        if not agents:
            if self.vb:
                print('failed to get agents')
            return
        agents=self._select_env(env)
        if not agents:
            return ''
        a, p=[a['useragent'] for a in agents], [float(a['share']) for a in agents] 
        r=random.choices(a, weights=p, k=1)[0]
        return r

from html.parser import HTMLParser
class H2TableAssociator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h2_text = None
        self.in_h2 = False
        
        self.tables_with_h2 = []  # list:tuple (h2_text, table_data)
        
        self.in_table = False
        self.current_table = []
        self.current_row = []
        self.in_th = False
        self.in_td = False
        self.current_cell = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.in_h2 = True
            self.h2_text = ''  # reset for new header
        elif tag == 'table':
            self.in_table = True
            self.current_table = []
        elif tag == 'tr' and self.in_table:
            self.current_row = []
        elif tag == 'th' and self.in_table:
            self.in_th = True
            self.current_cell = ''
        elif tag == 'td' and self.in_table:
            self.in_td = True
            self.current_cell = ''

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_h2 = False
            self.h2_text = self.h2_text.strip()
        elif tag == 'table' and self.in_table:
            # append current table with the latest header
            self.tables_with_h2.append((self.h2_text, self.current_table))
            self.in_table = False
        elif tag == 'tr' and self.in_table:
            self.current_table.append(self.current_row)
        elif tag == 'th' and self.in_table and self.in_th:
            self.current_row.append(self.current_cell.strip())
            self.in_th = False
        elif tag == 'td' and self.in_table and self.in_td:
            self.current_row.append(self.current_cell.strip())
            self.in_td = False

    def handle_data(self, data):
        if self.in_h2:
            self.h2_text += data
        elif self.in_th or self.in_td:
            self.current_cell += data