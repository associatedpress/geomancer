from json import JSONEncoder
import re
import us
from os.path import join, abspath, dirname
import csv

GAZDIR = join(dirname(abspath(__file__)), 'gazetteers')

class GeoType(object):
    """ 
    Base class for defining geographic types.
    All four static properties should be defined
    """
    human_name = None
    machine_name = None
    formatting_notes = None
    formatting_example = None
    validation_regex = None

    def as_dict(self):
        fields = [
            'human_name',
            'machine_name',
            'formatting_notes',
            'formatting_example',
        ]
        d = {k:getattr(self,k) for k in fields}
        for k,v in d.items():
            d[k] = ' '.join(v.split())
        return d

    def validate(self, values):
        ''' 
        Default is to implement a regex on a subclass that gets
        used here to validate the format. Optionally override this
        method to implement custom validation. If validation_regex
        is not defined on the subclass, this will always return True.

        values - A list (or other iterable) of values to evaluate

        Returns a boolean indicating whether all the members of the values
        list are valid and an optional user friendly message.
        '''

        if self.validation_regex is None:
            return False, None
        else:
            values = list(set([v for v in values if v]))
            for v in values:
                if not re.match(self.validation_regex, v):
                    message = 'The column you selected must be formatted \
                        like "%s" to match on %s geographies. Please pick another \
                        column or change the format of your data.' % \
                        (self.formatting_example, self.human_name)
                    return False, message
            return True, None
      
class GeoTypeEncoder(JSONEncoder):
    ''' 
    Custom JSON encoder so we can have nice things.
    '''
    def default(self, o):
        return o.as_dict()

class City(GeoType):
    human_name = 'City'
    machine_name = 'city'
    formatting_notes = 'City name followed by state name, postal abbreviation or \
        AP abbreviation.' 
    formatting_example = 'Chicago, Illinois; Chicago, IL or Chicago, Ill.'

   #def validate(self, values):
   #    ''' 
   #    Uses the US Census 2014 Place Name Gazetteer.
   #    https://www.census.gov/geo/maps-data/data/gazetteer2014.html
   #    '''
   #    gazetteer = set()
   #    with open(join(GAZDIR, 'place_names.csv'), 'rb') as f:
   #        reader = csv.reader(f)
   #        for row in reader:
   #            gazetteer.add(row[0].lower())
   #    values = set([v.split(',')[0].lower() for v in values if v])
   #    if values <= gazetteer:
   #        return True, None
   #    else:
   #        diffs = values - gazetteer
   #        return False, '"{0}" do not appear to be valid Census places'\
   #            .format(', '.join(diffs))

class State(GeoType):
    human_name = 'State'
    machine_name = 'state'
    formatting_notes = 'State name, postal abbreviation, or AP abbreviation.'
    formatting_example = 'Illinois, IL or Ill.'
    
    def validate(self, values):
        values = [v for v in values if v]
        non_matches = set()
        for val in values:
            st = us.states.lookup(val)
            if not st:
                st = [s for s in us.STATES if getattr(s, 'ap_abbr') == val]
            if not st:
                non_matches.add(val)
        if non_matches:
            return False, '"{0}" do not appear to be valid Census places'\
                .format(', '.join(non_matches))
        else:
            return True, None

class County(GeoType):
    human_name = 'County'
    machine_name = 'county'
    formatting_notes = 'Name of a U.S. County and state abbreviation.' 
    formatting_example = 'Cook County, IL'
    
    def validate(self, values):
        ''' 
        Uses the US Census 2014 County Gazetteer.
        https://www.census.gov/geo/maps-data/data/gazetteer2014.html
        '''
        gazetteer = set()
        with open(join(GAZDIR, 'county_names.csv'), 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                gazetteer.add(row[0].lower())
        vals = set()
        for val in values:
            val = val.lower()
            if 'county' not in val:
                val = u'{0} county'.format(val)
            vals.add(val)
        if vals <= gazetteer:
            return True, None
        else:
            diffs = vals - gazetteer
            return False, u'"{0}" do not appear to be valid Counties'\
                .format(u', '.join(diffs))

class SchoolDistrict(GeoType):
    human_name = 'School district'
    machine_name = 'school_district'
    formatting_notes = 'Name of an elementary, secondary or unified school district.'
    formatting_example = 'Chicago Public School District 299, IL'
    
    def validate(self, values):
        ''' 
        Uses the US Census 2014 Elementary, Secondary and Unified
        School District Gazetteers.
        https://www.census.gov/geo/maps-data/data/gazetteer2014.html
        '''
        gazetteer = set()
        with open(join(GAZDIR,'school_dists.csv'), 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                gazetteer.add(row[0].lower())
        values = set([v.split(',')[0].lower() for v in values if v])
        if values <= gazetteer:
            return True, None
        else:
            diffs = values - gazetteer
            return False, u'"{0}" do not appear to be valid School Districts'\
                .format(u', '.join(diffs))

class CongressionalDistrict(GeoType):
    human_name = 'Congressional district'
    machine_name = 'congress_district'
    formatting_notes = 'U.S Congressional District.' 
    formatting_example = 'Congressional District 7, IL'
    validation_regex = r'Congressional District \d+,.+'

class Zip5(GeoType):
    human_name = '5 digit zip code'
    machine_name = 'zip_5'
    formatting_notes = 'Five-digit U.S. Postal Service Zip Code.' 
    formatting_example = '60601'
    validation_regex = r'\d{5}$'

class Zip9(GeoType):
    human_name = '9 digit zip code'
    machine_name = 'zip_9'
    formatting_notes = 'Five-digit U.S. Postal Service Zip Code plus a four digit \
        geographic identifier.'
    formatting_example = '60601-3013'
    validation_regex = r'(\d{5})-(\d{4})$'

class StateFIPS(GeoType):
    human_name = 'FIPS: State'
    machine_name = 'state_fips'
    formatting_notes = 'Federal Information Processing (FIPS) code for a U.S. State.'
    formatting_example = '17'
    validation_regex = r'\d{2}$'

class StateCountyFIPS(GeoType):
    human_name = 'FIPS: County'
    machine_name = 'state_county_fips'
    formatting_notes = 'Federal Information Processing (FIPS) code for a U.S. County \
        which includes the FIPS code for the state.' 
    formatting_example = '17031'
    
    def validate(self, values):
        ''' 
        Uses the US Census 2014 County Gazetteers.
        https://www.census.gov/geo/maps-data/data/gazetteer2014.html
        '''
        gazetteer = set()
        with open(join(GAZDIR, 'county_names.csv'), 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                gazetteer.add(row[2].lower())
        values = set([v.split(',')[0].lower() for v in values if v])
        if values <= gazetteer:
            return True, None
        else:
            diffs = values - gazetteer
            return False, u'"{0}" do not appear to be valid County FIPS codes'\
                .format(u', '.join(diffs))

class CensusTract(GeoType):
    human_name = 'FIPS: Census Tract'
    machine_name = 'census_tract'
    formatting_notes = 'Federal Information Processing (FIPS) code for a U.S Census Tract' 
    formatting_example = '17031330100'
    validation_regex = r'\d{11}$'

