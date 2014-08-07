from flask import Blueprint, make_response, request, session, \
    render_template, current_app
import json
import os
import gzip
from uuid import uuid4
from werkzeug import secure_filename
from csvkit import convert
from csvkit.unicsv import UnicodeCSVReader
from cStringIO import StringIO

api = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = set(['csv', 'xls', 'xlsx'])

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

