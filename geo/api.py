from flask import Blueprint, make_response, request, jsonify, \
    session as flask_session
from geo.worker import DelayedResult, do_the_work
from geo.utils.lookups import GEO_TYPES
import json
from redis import Redis

redis = Redis()

api = Blueprint('api', __name__)

@api.route('/api/geomance/', methods=['POST', 'GET'])
def geomance_api():
    """ 
    Needs to get the file as well which fields have 
    geography and what kind of geography they contain.
    Should be a multipart POST with the file in the file part
    and the field definitions in the form part.

    Field definitions should be in string encoded JSON blob like so:

      {
        10: {
          'type': 'city_state', 
          'append_columns': ['total_population', 'median_age']
        }
      }
    The key is the zero-indexed position of the columns within the spreadsheet.
    The value is a dict containing the geographic type and the columns to 
    append. The values in that list should be fetched from one of the other
    endpoints.

    Responds with a key that can be used to poll for results
    """
    defs = json.loads(request.data)
    field_defs = {}
    for k,v in defs.items():
        field_defs[int(k)] = v
    if request.files:
        file_contents = request.files['input_file'].read()
    else:
        file_contents = flask_session['file']
    session = do_the_work.delay(file_contents, field_defs)
    resp = make_response(json.dumps({'session_key': session.key}))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/geomance-results/<session_key>/')
def geomance_results(session_key):
    """ 
    Looks in the Redis queue to see if the worker has finished yet.
    """
    rv = DelayedResult(session_key)
    if rv.return_value is None:
        return jsonify(ready=False)
    redis.delete(session_key)
    return jsonify(ready=True, result=rv.return_value)

@api.route('/api/geo-types/')
def geo_types():
    """ 
    Return a list of supported geography types
    Optionally include a 'name', 'description', or 'acs_sumlev' 
    to limit response
    """
    types = []
    if request.args.get('name'):
        name = request.args['name'].lower()
        types = [r for r in GEO_TYPES if name in r['name'].lower()]
    elif request.args.get('description'):
        desc = request.args['description'].lower()
        types = [r for r in GEO_TYPES if desc in r['description'].lower()]
    elif request.args.get('acs_sumlev'):
        sumlev = request.args['acs_sumlev'].lower()
        types = [r for r in GEO_TYPES if sumlev in r['acs_sumlev'].lower()]
    else:
        types = GEO_TYPES
    resp = make_response(json.dumps(types))
    resp.headers['Content-Type'] = 'application/json'
    return resp
    

@api.route('/api/<geo_type>/')
def data_attrs(geo_type):
    """ 
    For a given geographic type, return a list of available data attributes
    for that geography.
    """
    resp = make_response(json.dumps({}))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@api.route('/api/data-map/')
def data_map(geo_type):
    """ 
    For a list of geographic identifiers, a geographic type and data attributes, 
    return a set of data attributes for each gepgraphic identifier
    """
    resp = make_response(json.dumps({}))
    resp.headers['Content-Type'] = 'application/json'
    return resp
