import scrapelib
from urllib import urlencode
import json
import os
from geomancer.helpers import encoded_dict
from geomancer.mancers.base import BaseMancer, MancerError
from geomancer.app_config import CACHE_DIR
from string import punctuation
import re

SUMLEV_LOOKUP = {
    "city": "160,170,060",
    "state": "040",
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

class CensusReporter(BaseMancer):
    """ 
    Subclassing the main BaseMancer class
    """
    
    base_url = 'http://api.censusreporter.org/1.0'
    
    info_url = 'http://censusreporter.org'
    description = """ 
        Demographic data from the 2013 American Community.
    """

    @staticmethod
    def column_info():
        base_url = 'http://api.censusreporter.org/1.0'
        table_ids = [
            "B01003",
            "B19013",
            "B19301",
            "B02001",
            "B01002",
            "B15002",
            "B25077",
            "B26001",
            "B11009",
            "B05006"
        ]
        scraper = scrapelib.Scraper()
        scraper.cache_storage = scrapelib.cache.FileCache(CACHE_DIR)
        scraper.cache_write_only = False
        columns = []
        for table in table_ids:
            info = scraper.urlopen('%s/table/%s' % (base_url, table))
            table_info = json.loads(info)
            d = {
                'table_id': table,
                'human_name': table_info['table_title'],
                'description': '',
                'source_url': 'http://censusreporter.org/tables/%s/' % table,
                'geo_types': SUMLEV_LOOKUP.keys(),
                'count': len(table_info['columns'].keys())
            }
            columns.append(d)
        return columns

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
            if geo_type == 'zip_5':
                q_dict['q'] = search_term.zfill(5)
        q_dict = encoded_dict(q_dict)
        params = urlencode(q_dict)
        try:
            response = self.urlopen('%s/geo/search?%s' % (self.base_url, params))
        except scrapelib.HTTPError, e:
            try:
                body = json.loads(e.body.json()['error'])
            except ValueError:
                body = None
            raise MancerError('Census Reporter API returned a %s status' \
                % response.status_code, body=body)
        results = json.loads(response)
        try:
            results = {
                'term': search_term,
                'geoid': results['results'][0]['full_geoid']
            }
        except IndexError:
            results = {
                'term': search_term,
                'geoid': None,
            }
        return results
   
    def _chunk_geoids(self, geo_ids):
        for i in xrange(0, len(geo_ids), 100):
            yield geo_ids[i:i+100]

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
        results = {'header': []}
        for gids in self._chunk_geoids(geo_ids):
            query = {
                'table_ids': ','.join(columns),
                'geo_ids': ','.join([g[1] for g in gids]),
            }
            params = urlencode(query)
            try:
                response = self.urlopen('%s/data/show/latest?%s' % (self.base_url, params))
            except scrapelib.HTTPError, e:
                try:
                    body = json.loads(e.body.json()['error'])
                except ValueError:
                    body = None
                except AttributeError:
                    body = e.body
                raise MancerError('Census Reporter API returned an error', body=body)
            raw_results = json.loads(response)
            for geo_type, geo_id in gids:
                if not results.get(geo_id):
                    results[geo_id] = []
                for table_id in columns:
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
