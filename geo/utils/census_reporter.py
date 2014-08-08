import scrapelib
from urllib import urlencode
import json
import os
from geo.app_config import CACHE_DIR

class CensusReporterError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message

class CensusReporter(scrapelib.Scraper):
    """ 
    Subclassing scrapelib here mainly to take advantage of pluggable caching backend.
    """
    
    def __init__(self,
                 raise_errors=True,
                 requests_per_minute=0,
                 retry_attempts=5,
                 retry_wait_seconds=1,
                 header_func=None, 
                 cache_dir=CACHE_DIR):
        self.base_url = 'http://api.censusreporter.org/1.0'
        
        super(CensusReporter, self).__init__(raise_errors=raise_errors,
                                             requests_per_minute=requests_per_minute,
                                             retry_attempts=retry_attempts,
                                             retry_wait_seconds=retry_wait_seconds,
                                             header_func=header_func)
        
        # We might want to talk about configuring an S3 backed cache for this
        # so we don't run the risk of running out of disk space. 
        self.cache_storage = scrapelib.cache.FileCache(cache_dir)

    def geo_search(self, search_term):
        """ 
        Search for geoids based upon name of geography
        """
        params = urlencode({'q': search_term})
        try:
            response = self.urlopen('%s/geo/search?%s' % (self.base_url, params))
        except scrapelib.HTTPError, e:
            raise CensusReporterError('Census Reporter API returned %s' % e.body)
        results = json.loads(response)
        return results

    def data_show(self, acs='latest', table_ids=None, geo_ids=None):
        """ 
        Fetch data from given ACS release based upon the table_ids and geo_ids
        """
        query = {
            'table_ids': ','.join(table_ids),
            'geo_ids': ','.join(geo_ids),
        }
        params = urlencode(query)
        try:
            response = self.urlopen('%s/data/show/%s?%s' % (self.base_url, acs, params))
        except scrapelib.HTTPError, e:
            raise CensusReporterError('Census Reporter API returned %s' % e.body)
        results = json.loads(response)
        return results
