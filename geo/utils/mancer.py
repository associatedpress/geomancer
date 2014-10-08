import scrapelib
from urllib import urlencode
import json
import os
from geo.app_config import CACHE_DIR
from geo.utils.helpers import encoded_dict
from string import punctuation
import re

class MancerError(Exception):
    def __init__(self, message, body=None):
        Exception.__init__(self, message)
        self.message = message
        self.body = body

class Mancer(scrapelib.Scraper):
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
        
        super(Mancer, self).__init__(raise_errors=raise_errors,
                                             requests_per_minute=requests_per_minute,
                                             retry_attempts=retry_attempts,
                                             retry_wait_seconds=retry_wait_seconds,
                                             header_func=header_func)
        
        # We might want to talk about configuring an S3 backed cache for this
        # so we don't run the risk of running out of disk space. 
        self.cache_storage = scrapelib.cache.FileCache(cache_dir)
        self.cache_write_only = False

    @staticmethod
    def column_info():
        """ 
        This returns a list of dicts containing info about datasets that can be
        returned by the API. This needs to be a static method so that the
        application layer can use it to compile a list of columns that can be
        appended to incoming spreadsheets.  
        
        Should look like this:

        [
            {
              'table_id': '<unique_id>', 
              'human_name': '<human_friendly_name>',
              'description': '<free form text description>',
              'source_url': '<where to find source on the web>',
            },
            {
              'table_id': '<unique_id>', 
              'human_name': '<human_friendly_name>',
              'description': '<free form text description>',
              'source_url': '<where to find source on the web>',
            },
            ...etc...
        ]
        """

        raise NotImplementedError

    def geo_lookup(self, search_term, geo_type=None):
        """ 
        Method for looking up geographies through specific APIs, if needed
        Should be implemented by subclasses

        'search_term' is the string that will be used to search
        'geo_type' is one of the 13 geographic types that we support
            ('city', 'state', 'congress_district', ...etc...)
            This can be used by subclasses to narrow the search in a way that 
            is specific to that API
        
        Returns a response that maps the incoming search term to the
        geographic identifier to be used with the search method:

        {
          'term': <search_term>,
          'geoid': '<full_geoid>',
        }
        
        Default behavior is to just echo back the search_term as the geoid.
        This makes it possible to create a common interface for all subclasses
        without needing to figure out if you need to search or not.
        """

        return {'term': search_term, 'geoid': search_term}

    def search(self, geo_ids=None, columns=None):
        """
        This method should send the search request to the API endpoint(s).
        'geo_ids' is a list of geo_ids returned by the geo_lookup method
        'columns' is a list of columns to return. Child classes should 
        be capable of looking these up in a way that makes sense to the API.
        
        Response looks like this:
        {
            'header': [
                '<data source name 1>',
                '<data source name 2>',
                '...etc...'
            ],
            '<geographic id 1>': [
                <value 1>,
                <value 2>,
                <value 3>,
                <value 4>,
                ...etc...,
            ],
            '<geographic id 2>': [
                <value 1>,
                <value 2>,
                <value 3>,
                <value 4>,
                ...etc...,
            ],
        }
        
        One should be able to call the python zip function on the header list 
        and any of the lists with data about the geographies and have it work.
        """
        raise NotImplementedError
