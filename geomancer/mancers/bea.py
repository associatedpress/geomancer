from urllib import urlencode
import json
import os
from geomancer.app_config import MANCER_KEYS
from geomancer.helpers import encoded_dict
from geomancer.mancers.geotype import State, StateFIPS
from geomancer.mancers.base import BaseMancer, MancerError
from string import punctuation
import re
from urlparse import urlparse
import us

class BureauEconomicAnalysis(BaseMancer):
    """ 
    Subclassing the main BaseMancer class
    """

    name = 'Bureau of Economic Analysis'
    machine_name = 'bureau_economic_analysis'
    base_url = 'http://www.bea.gov/api/data'
    info_url = 'http://www.bea.gov'
    description = """ 
        GDP & Personal Income Data (2013) from the Bureau of Economic Analysis
    """
    api_key_required = True

    def __init__(self, api_key=None):
        self.api_key = api_key
        BaseMancer.__init__(self)

    def column_info(self):
        columns = [
            {
                'table_id': 'GDP_SP',
                'human_name': 'Nominal GDP',
                'description': '2013 Gross Domestic Product (GDP) (state annual product)',
                'source_name': self.name,
                'source_url': 'http://bea.gov/regional/index.htm',
                'geo_types': [State()],
                'columns': ['2013 GDP'],
                'count': 1
            },
            {
                'table_id': 'RGDP_SP',
                'human_name': 'Real GDP',
                'description': '2013 Real GDP (state annual product)',
                'source_name': self.name,
                'source_url': 'http://bea.gov/regional/index.htm',
                'geo_types': [State()],
                'columns': ['2013 Real GDP'],
                'count': 1
            },
            {
                'table_id': 'PCRGDP_SP',
                'human_name': 'Real GDP - Per Capita',
                'description': '2013 Per capita Real GDP (state annual product)',
                'source_name': self.name,
                'source_url': 'http://bea.gov/regional/index.htm',
                'geo_types': [State()],
                'columns': ['2013 Per Capita Real GDP'],
                'count': 1
            },
            {
                'table_id': 'TPI_SI',
                'human_name': 'Personal Income - Total',
                'description': '2013 Total Personal Income (state annual income)',
                'source_name': self.name,
                'source_url': 'http://bea.gov/regional/index.htm',
                'geo_types': [State()],
                'columns': ['2013 Total Personal Income'],
                'count': 1
            },
            {
                'table_id': 'PCPI_SI',
                'human_name': 'Personal Income - Per Capita',
                'description': '2013 Per Capita personal income (state annual income)',
                'source_name': self.name,
                'source_url': 'http://bea.gov/regional/index.htm',
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
        regex = re.compile('[%s]' % re.escape(punctuation))
        search_term = regex.sub('', search_term)
        if geo_type == 'state':
            return {'term': search_term, 'geoid': self.lookup_state_name(search_term)}
        else:
            return {'term': search_term, 'geoid': search_term}

    def search(self, geo_ids=None, columns=None):

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
