import scrapelib
from urllib import urlencode
import json
import os
from geo.utils.helpers import encoded_dict
from geo.utils.mancer import Mancer
from string import punctuation
import re

SUMLEV_LOOKUP = {
    "city": "160,170,060",
    "state": "040",
    "postal": "160,170,060",
    "state_fips": "040",
    "state_county_fips":"050",
    "zip_5": "850,860",
    "zip_9": "850,860",
    #"state_postal": "040",
    "county": "050",
    "school_district": "950,960,970",
    "congress_district": "500", # Assuming US Congressional District
    "census_tract": "140",
    "census_blockgroup": "150",
    "census_block": "101",
}

ACS_DATA_TYPES = {
    "total_pop": {
        "human_name": "Total population",
        "table_id": "B01003",
        "count" : 1,
    },
    "median_hh_income": {
        "human_name": "Median household income",
        "table_id": "B19013",
        "count" : 1,
    },
    "per_capita_income": {
        "human_name": "Per capita income",
        "table_id": "B19301",
        "count" : 1,
    },
    "pop_percent_by_race": {
        "human_name": "Population percentage by race",
        "table_id": "B02001", 
        "count" : 10,
    },
    # This is going to need to be derived from something else
    # "percent_minority": "",
    "median_age": {
        "human_name": "Median age",
        "table_id": "B01002",
        "count" : 4,
    },
    "education": {
        "human_name": "Educational attainment",
        "table_id": "B15002",
        "count" : 35,
    },
    "median_val_oo_housing": {
        "human_name": "Median value owner occupied housing",
        "table_id": "B25077",
        "count" : 1,
    },
    "group_quarters_pop": {
        "human_name": "Group quarters population",
        "table_id": "B26001",
        "count" : 1,
    },
    "unmarried_hh_by_sex": {
        "human_name": "Unmarried-partner households by sex of partner",
        "table_id": "B11009",
        "count" : 7,
    },
    "place_of_birth": {
        "human_name": "Place of birth (foreign-born population)",
        "table_id": "B05006",
        "count" : 161,
    },
}

class CensusReporterError(Exception):
    def __init__(self, message, body=None):
        Exception.__init__(self, message)
        self.message = message
        self.body = body

class CensusReporter(Mancer):
    """ 
    Subclassing the main Mancer class
    """
    
    base_url = 'http://api.censusreporter.org/1.0'
    
    def geo_lookup(self, search_term, geo_type=None):
        """ 
        Search for geoids based upon name of geography
        'sumlevs' is an optional comma seperated string with ACS Summary levels

        Returns a response that maps the incoming search term to the geoid:

        {
          'term': <search_term>,
          'geoid': '<full_geoid>',
        }

        """
        regex = re.compile('[%s]' % re.escape(punctuation))
        search_term = regex.sub('', search_term)
        q_dict = {'q': search_term}
        if geo_type:
            q_dict['sumlevs'] = SUMLEV_LOOKUP[geo_type]
        q_dict = encoded_dict(q_dict)
        params = urlencode(q_dict)
        try:
            response = self.urlopen('%s/geo/search?%s' % (self.base_url, params))
        except scrapelib.HTTPError, e:
            try:
                body = json.loads(e.body.json()['error'])
            except ValueError:
                body = None
            raise CensusReporterError('Census Reporter API returned a %s status' \
                % response.status_code, body=body)
        results = json.loads(response)
        return {
            'term': search_term,
            'geoid': results['results'][0]['full_geoid']
        }

    def search(self, geo_ids=None, columns=None):
        """ 
        Response should look like:
        {
            'header': [
                'Sex by Educational Attainment for the Population 25 Years and Over, 5th and 6th grade',
                'Sex by Educational Attainment for the Population 25 Years and Over, 7th and 8th grade'
                '...etc...'
            ],
            '04000US55': [
                1427.0,
                723.0,
                3246.0,
                760.0,
                ...etc...,
            ],
            '04000US56': [
                1567.0,
                743.0,
                4453.0,
                657.0,
                ...etc...,
            ]
        }

        The keys are CensusReporter 'geo_ids' and the value is a list that you
        should be able to call the python 'zip' function on with the 'header' key.
        """

        table_ids = [ACS_DATA_TYPES[c]['table_id'] for c in columns]
        query = {
            'table_ids': ','.join(table_ids),
            'geo_ids': ','.join(geo_ids),
        }
        params = urlencode(query)
        try:
            response = self.urlopen('%s/data/show/latest?%s' % (self.base_url, params))
        except scrapelib.HTTPError, e:
            try:
                body = json.loads(e.body.json()['error'])
            except ValueError:
                body = None
            raise CensusReporterError('Census Reporter API returned a %s status' \
                % response.status_code, body=body)
        raw_results = json.loads(response)
        results = {'header': []}
        for geo_id in geo_ids:
            results[geo_id] = []
            for table_id in table_ids:
                table_info = raw_results['tables'][table_id]
                title = table_info['title']
                detail_ids = [k for k in table_info['columns'].keys() \
                    if table_info['columns'][k].get('indent') is not None]
                denominator = table_info['denominator_column_id']
                for detail_id in detail_ids:
                    table_title = table_info['title']
                    column_title = None
                    detail_title = table_info['columns'][detail_id]['name']
                    column_title = '%s, %s' % (table_title, detail_title,)
                    if column_title not in results['header']:
                        results['header'].extend([column_title, '%s (error margin)' % column_title])
                    detail_info = raw_results['data'][geo_id][table_id]
                    results[geo_id].extend([
                        detail_info['estimate'][detail_id], 
                        detail_info['error'][detail_id],
                    ])
        return results
