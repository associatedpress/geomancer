import scrapelib
from urllib import urlencode
import json
import os
import us
from geomancer.helpers import encoded_dict
from geomancer.mancers.base import BaseMancer, MancerError
from geomancer.mancers.geotype import City, State, StateFIPS, StateCountyFIPS, \
    Zip5, Zip9, County, SchoolDistrict, CongressionalDistrict, CensusTract
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
}

class CensusReporter(BaseMancer):
    """ 
    Subclassing the main BaseMancer class
    """
    
    name = 'Census Reporter'
    machine_name = 'census_reporter'
    base_url = 'http://api.censusreporter.org/1.0'
    info_url = 'http://censusreporter.org'
    description = """ 
        Demographic data from the 2013 American Community Survey.
    """

    def get_metadata(self):
        table_ids = [
            "B01003", # Total Population
            "B19013", # Median Household Income
            "B19301", # Per Capita Income
            "B02001", # Race
            "B01002", # Median Age by Sex"
            "B25077", # Median Value (Dollars)
            "B26001", # Group Quarters Population
            "B11009", # Unmarried-partner Households by Sex of Partner
            "B05006", # Place of Birth for the Foreign-born Population in the United States
            "B19083", # Gini Index of Income Inequality
            "B15003", # Educational Attainment
            "B03002", # Hispanic or Latino Origin by Race
        ]
        columns = []
        for table in table_ids:
            info = self.urlopen('%s/table/%s' % (self.base_url, table))
            table_info = json.loads(info)
            d = {
                'table_id': table,
                'human_name': table_info['table_title'],
                'description': '',
                'source_name': self.name,
                'source_url': 'http://censusreporter.org/tables/%s/' % table,
                'geo_types': [City(), State(), StateFIPS(), StateCountyFIPS(), Zip5(), 
                    Zip9(), County(), SchoolDistrict(), 
                    CongressionalDistrict(), CensusTract()],
                'columns': [v['column_title'] for v in table_info['columns'].values() if v['indent'] is not None]
            }

            d['columns'].extend(['%s (error margin)' % v for v in d['columns']])
            d['columns'] = sorted(d['columns'])
            
            if table == 'B25077': # Overriding the name for "Median Value" table
                d['human_name'] = 'Median Value, Owner-Occupied Housing Units'
                d['columns'] = ['Median Value, Owner-Occupied Housing Units', 
                                'Median Value, Owner-Occupied Housing Units (error margin)']
            
            d['count'] = len(d['columns'])
            columns.append(d)
        return columns

    def lookup_state(self, term, attr='name'):
        st = us.states.lookup(term)
        if not st:
            st = [s for s in us.STATES if getattr(s, 'ap_abbr') == term]
        if st:
            return getattr(st, attr)
        else:
            return term

    def geo_lookup(self, search_term, geo_type=None):
        """ 
        Search for geoids based upon name of geography

        Returns a response that maps the incoming search term to the geoid:

        {
          'term': <search_term>,
          'geoid': '<full_geoid>',
        }

        """
        if geo_type == 'congress_district':
            geoid = None
            dist, st = search_term.rsplit(',', 1)
            fips = self.lookup_state(st.strip(), attr='fips')
            try:
                dist_num = str(int(dist.split(' ')[-1]))
            except ValueError:
                dist_num = '00'
            if fips and dist_num:
                geoid = '50000US{0}{1}'\
                    .format(fips, dist_num.zfill(2))
            return {
                'term': search_term,
                'geoid': geoid
            }
        regex = re.compile('[%s]' % re.escape(punctuation))
        search_term = regex.sub('', search_term)
        if geo_type in ['census_tract', 'state_fips']:
            return {
                'term': search_term,
                'geoid': '%s00US%s' % (SUMLEV_LOOKUP[geo_type], search_term)
            }
        if geo_type == 'state_county_fips':
            resp = {
                'term': search_term,
                'geoid': None
                }
            g = StateCountyFIPS()
            valid, message = g.validate([search_term])
            if valid:
                resp['geoid'] = '05000US%s' % search_term
            return resp
        q_dict = {'q': search_term}
        if geo_type:
            q_dict['sumlevs'] = SUMLEV_LOOKUP[geo_type]
            if geo_type == 'zip_5':
                q_dict['q'] = search_term.zfill(5)
            if geo_type == 'state':
                q_dict['q'] = self.lookup_state(search_term)
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

    def _try_search(self, gids, columns, bad_gids=[]):
        query = {
            'table_ids': ','.join(columns),
            'geo_ids': ','.join(sorted([g[1] for g in gids])),
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
            if 'The ACS 2013 5-year release doesn\'t include GeoID(s)' in body:
                error = json.loads(body)
                bad_gids.append(error['error'].rsplit(' ',1)[1].replace('.', ''))
                for idx,gid in enumerate(gids):
                    if gid[1] in bad_gids:
                        gids.pop(idx)
                response = self._try_search(gids, columns, bad_gids=bad_gids)
            else:
                raise MancerError('Census Reporter API returned an error', body=body)
        return response


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
        # these are the tables where we want to leave the table name out
        # of the header cell name in output, for prettiness, b/c
        # there is redundant info in table_title & detail_title
        table_name_exceptions = [   'Median Household Income in the Past 12 Months (In 2013 Inflation-adjusted Dollars)',
                                    'Per Capita Income in the Past 12 Months (In 2013 Inflation-adjusted Dollars)',
                                    ]

        results = {'header': []}
        for gids in self._chunk_geoids(geo_ids):
            raw_results = self._try_search(gids, columns)
            raw_results = json.loads(raw_results)
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
                        if table_title in table_name_exceptions:
                            column_title = detail_title
                        elif table_id == 'B25077':
                            column_title = 'Median Value, Owner-Occupied Housing Units'
                        else:
                            column_title = '%s, %s' % (table_title, detail_title,)
                        if column_title not in results['header']:
                            results['header'].extend([column_title, '%s (error margin)' % column_title])

                        detail_info = raw_results['data'][geo_id][table_id]
                        results[geo_id].extend([
                            detail_info['estimate'][detail_id], 
                            detail_info['error'][detail_id],
                        ])
        return results
