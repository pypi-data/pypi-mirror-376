import unittest

class TestNotebook(unittest.TestCase):
    
    def setUp(self):
        import importlib
        import randomagent.useragents as us
        us=importlib.reload(us)
        self.ua=us.Useragents()
    
    def tearDown(self):
        del self.ua

    def test_get_user_agent(self):
        a=self.ua.get_user_agent()
        assert isinstance(a, str)
        assert bool(a)
        assert 'Mozilla' in a
    
    def test_get_user_agents(self):
        a=self.ua.get_user_agents()
        assert isinstance(a, dict)
        assert a.keys()
        assert len(a)>3
        envs=['Most Common Desktop Useragents', 'Most Common Mobile Useragents', 'Latest Windows Desktop Useragents', 'Latest Mac OS X Desktop Useragents', 'Latest Linux Desktop Useragents', 'Latest iPhone Useragents', 'Latest iPod Useragents', 'Latest iPad Useragents', 'Latest Android Mobile Useragents']
        assert sum([t in a.keys() for t in envs])>2
