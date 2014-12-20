import scrapelib
from urllib import urlencode
import json
import os
from geomancer.app_config import CACHE_DIR, MANCER_KEYS
from geomancer.helpers import encoded_dict
from geomancer.mancers.geotype import State, StateFIPS
from string import punctuation
import re
from urlparse import urlparse
import us

class BureauEconomicAnalysis(scrapelib.Scraper):
    """ 
    Subclassing the main BaseMancer class
    """

    name = 'Bureau of Economic Analysis'
    machine_name = 'bureau_economic_analysis'
    base_url = 'http://www.bea.gov/api/data'
    info_url = 'http://www.bea.gov'
    api_key = MANCER_KEYS[machine_name]
    description = """ 
        GDP by state (2013) from the Bureau of Economic Analysis
    """

    def column_info(self):
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
              'source_name': '<name of data source>',
              'source_url': '<where to find source on the web>',
              'geo_types': ['list', 'of', 'instances', 'of', GeoType()],
              'count': '<number of columns this will add to spreadsheet>',
              'columns': ['list', 'of', 'column', 'names', 'that', 'will', 'be', 'appended']
            },
            {
              'table_id': '<unique_id>', 
              'human_name': '<human_friendly_name>',
              'description': '<free form text description>',
              'source_name': '<name of data source>',
              'source_url': '<where to find source on the web>',
              'geo_types': ['examples', Zip5(), State(), County()],
              'count': '<number of columns this will add to spreadsheet>',
              'columns': ['list', 'of', 'column', 'names', 'that', 'will', 'be', 'appended']
            },
            ...etc...
        ]

        """
        columns = [
            {
                'table_id': 'GDP_SP',
                'human_name': '2013 GDP',
                'description': '2013 Gross Domestic Product (GDP) (state annual product)',
                'source_name': self.name,
                'source_url': '', #populate this
                'geo_types': [State()], #is this right
                'columns': ['2013 GDP'],
                'count': 1
            },
            {
                'table_id': 'RGDP_SP',
                'human_name': '2013 Real GDP',
                'description': '2013 Real GDP (state annual product)',
                'source_name': self.name,
                'source_url': '', #populate this
                'geo_types': [State()],
                'columns': ['2013 Real GDP'],
                'count': 1
            },
            {
                'table_id': 'PCRGDP_SP',
                'human_name': '2013 Per Capita Real GDP',
                'description': '2013 Per capita Real GDP (state annual product)',
                'source_name': self.name,
                'source_url': '', #populate this
                'geo_types': [State()],
                'columns': ['2013 Per Capita Real GDP'],
                'count': 1
            },
            {
                'table_id': 'TPI_SI',
                'human_name': '2013 Total Personal Income',
                'description': '2013 Total Personal Income (state annual income)',
                'source_name': self.name,
                'source_url': '', #populate this
                'geo_types': [State()],
                'columns': ['2013 Total Personal Income'],
                'count': 1
            },
            {
                'table_id': 'PCPI_SI',
                'human_name': '2013 Per Capita Personal Income',
                'description': '2013 "Per Capita personal income (state annual income)',
                'source_name': self.name,
                'source_url': '', #populate this
                'geo_types': [State()],
                'columns': ['2013 Per Capita Personal Income'],
                'count': 1
            }
        ]

        return columns

    def lookup_state_name(self, term):
        st = us.states.lookup(term)
        if not st:
            st = [s for s in us.STATES if getattr(s, 'ap_abbr') == term]
        if st:
            return st.name
        else:
            return term

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
          'geo_type': '<geo_type>',
        }
        
        Default behavior is to just echo back the search_term as the geoid.
        This makes it possible to create a common interface for all subclasses
        without needing to figure out if you need to search or not.
        """
        regex = re.compile('[%s]' % re.escape(punctuation))
        search_term = regex.sub('', search_term)
        if geo_type == 'state':
            return {'term': search_term, 'geoid': self.lookup_state_name(search_term)}
        else: # finish this
            return {'term': search_term, 'geoid': search_term}

    def search(self, geo_ids=None, columns=None):
        """
        This method should send the search request to the API endpoint(s).
        'geo_ids' is a list of tuples with the geography type and geo_id
        returned by the geo_lookup method like so:

        [
            ('state', 'IL',),
            ('state', 'CA',),
            ...etc...
        ]

        'columns' is a list of columns to
        return. Child classes should be capable of looking these up in a way
        that makes sense to the API.
        
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

        column_names = {
        'GDP_SP': '2013 GDP (millions)',
        'RGDP_SP': '2013 Real GDP (millions of chained 2009 dollars)',
        'PCRGDP_SP': '2013 Per Capita Real GDP (chained 2009 dollars)',
        'TPI_SI': '2013 Total Personal Income (thousands of dollars)',
        'PCPI_SI': '2013 Per Capita Personal Income (dollars)'
        }

        results = {'header':[]}

        for col in columns:
            url = self.base_url+'/?UserID=%s&method=GetData&datasetname=RegionalData&KeyCode=%s&Year=2013&ResultFormat=json' %(self.api_key, col)
            try:
                response = self.urlopen(url)
            except scrapelib.HTTPError, e:
                try:
                    body = json.loads(e.body.json()['error'])
                except ValueError:
                    body = None
                except AttributeError:
                    body = e.body
                raise MancerError('BEA API returned an error', body=body)
            raw_results = json.loads(response)
            raw_data = raw_results['BEAAPI']['Results']['Data']
            results['header'].append(column_names[col])
            for geo_type, geo_id in geo_ids:
                if not results.get(geo_id):
                    results[geo_id] = []
                if geo_type == 'state': #### handle state fips?
                    for geo_data in raw_data: #this is not efficient...make this better
                        if geo_data['GeoName'] == geo_id:
                            results[geo_id].append(geo_data['DataValue'])
                            break
        return results
