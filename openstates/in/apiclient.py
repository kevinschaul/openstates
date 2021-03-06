import os
import requests
import urlparse
import functools


def check_response(method):
    '''Decorated functions will run, and if they come back
    with a 429 and retry-after header, will wait and try again.
    '''
    @functools.wraps(method)
    def wrapped(self, *args, **kwargs):
        resp = method(self, *args, **kwargs)
        status = resp.status_code
        if 400 < status:
            if resp.status_code == 429:
                self.handle_429(resp, *args, **kwargs)
                return method(self, *args, **kwargs).json()
            raise Exception('Bad api response: %r %r %r' % (resp, resp.text, resp.headers))
        return resp.json()
    return wrapped


class ApiClient(object):
    '''
    docs: http://docs.api.iga.in.gov/
    '''
    root = "https://api.iga.in.gov/"
    resources = dict(
        sessions='/sessions',
        subjects='/{session}/subjects',
        chambers='/{session}/chambers',
        bills='/{session}/bills',
        chamber_bills='/{session}/chambers/{chamber}/bills',
        committees='/{session}/committees',
        committee='/{session}/committees/{committee_name}',
        legislators='/{session}/legislators',
        legislator='/{session}/legislators/{legislator_id}',
        chamber_legislators='/{session}/chambers/{chamber}/legislators',
        )

    def __init__(self, scraper):
        self.scraper = scraper
        self.apikey = os.environ['INDIANA_API_KEY']


    @check_response
    def geturl(self, url):
        headers = {}
        headers['Authorization'] = self.apikey
        headers['Accept'] = "application/json"
        self.scraper.info('Api GET next page: %r, %r' % (url, headers))
        return self.scraper.get(url, headers=headers, verify=False)

    @check_response
    def get_relurl(self, url):
        headers = {}
        headers['Authorization'] = self.apikey
        headers['Accept'] = "application/json"
        url = urlparse.urljoin(self.root, url)
        self.scraper.info('Api GET: %r, %r' % (url, headers))
        return self.scraper.get(url, headers=headers, verify=False)

    def make_url(self, resource_name, **url_format_args):
        # Build up the url.
        url = self.resources[resource_name]
        url = url.format(**url_format_args)
        url = urlparse.urljoin(self.root, url)
        return url

    @check_response
    def get(self, resource_name, requests_args=None,
            requests_kwargs=None, **url_format_args):
        '''Resource is a self.resources dict key.
        '''
        url = self.make_url(resource_name, **url_format_args)

        # Add in the api key.
        requests_args = requests_args or ()
        requests_kwargs = requests_kwargs or {}
        requests_kwargs.update(verify=False)
        headers = requests_kwargs.get('headers', {})
        headers['Authorization'] = self.apikey
        headers['Accept'] = "application/json"
        requests_kwargs['headers'] = headers

        args = (url, requests_args, requests_kwargs)
        self.scraper.info('Api GET: %r, %r, %r' % args)
        return self.scraper.get(url, *requests_args, **requests_kwargs)

    def unpaginate(self, result):
        for data in result['items']:
            yield data
        while True:
            if 'nextLink' in result:
                url = result['nextLink']
                self.scraper.info('Api GET next page: %r' % url)
                result = self.get_relurl(url)
                if not result['items']:
                    return
                for data in result['items']:
                    yield data
            else:
                return

    def handle_429(self, resp, *args, **kwargs):
        '''According to the docs:

        "If the rate limit is exceeded, we will respond with a HTTP 429 Too Many
        Requests response code and a body that details the reason for the rate
        limiter kicking in. Further, the response will have a Retry-After
        header that tells you for how many seconds to sleep before retrying.
        You should anticipate this in your API client for the smoothest user
        experience."
        '''
        seconds = int(resp.headers['retry-after'])
        self.scraper.info('Got a 429: Sleeping %s seconds per retry-after header.' % seconds)
        time.sleep(seconds)
