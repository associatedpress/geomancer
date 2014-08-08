from flask import Blueprint, make_response, request
import json

api = Blueprint('api', __name__)

@api.route('/api/geomance/', methods=['POST', 'GET'])
def geomance_api():
    """ 
    Needs to get the file as well which fields have 
    geography and what kind of geography they contain.
    Should be a multipart POST with the file in the file part
    and the field definitions in the form part.

    Field definitions should be in string encoded JSON blob like so:

    [
      {
        'name', 'Residence', 
        'type': 'city_state', 
        'append_columns': ['total_population', 'median_age']
      },
    ]
    """
    print request.form
    resp = make_response(json.dumps({}))
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
