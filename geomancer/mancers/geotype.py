class GeoType(object):
    """ 
    Base class for defining geographic types.
    All three static properties should be defined
    """
    human_name = None
    machine_name = None
    description = None

    def as_dict(self):
        return {k:getattr(self,k) for k in \
            ['human_name','machine_name','description']}

class City(GeoType):
    human_name = 'City or U.S. Census Place'
    machine_name = 'city'
    description = ''

class State(GeoType):
    human_name = 'U.S. State'
    machine_name = 'state'
    description = ''

class StateFIPS(GeoType):
    human_name = 'U.S. State FIPS code'
    machine_name = 'state_fips'
    description = ''

class StateCountyFIPS(GeoType):
    human_name = 'U.S. State + County FIPS code'
    machine_name = 'state_county_fips'
    description = ''

class Zip5(GeoType):
    human_name = '5-digit Zip Code'
    machine_name = 'zip_5'
    description = ''

class Zip9(GeoType):
    human_name = '9-digit Zip Code'
    machine_name = 'zip_9'
    description = ''

class County(GeoType):
    human_name = 'County'
    machine_name = 'county'
    description = ''

class SchoolDistrict(GeoType):
    human_name = 'school_district'
    machine_name = 'school_district'
    description = ''

class CongressionalDistrict(GeoType):
    human_name = 'U.S. Congressional District'
    machine_name = 'congress_district'
    description = ''

class CensusTract(GeoType):
    human_name = 'U.S. Census Tract'
    machine_name = 'census_tract'
    description = ''

class CensusBlockGroup(GeoType):
    human_name = 'U.S. Census Block Group'
    machine_name = 'census_block_group'
    description = ''

class CensusBlock(GeoType):
    human_name = 'U.S. Census Block'
    machine_name = 'census_block'
    description = ''
