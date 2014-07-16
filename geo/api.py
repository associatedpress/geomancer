from flask import Blueprint, make_response, request
import json

api = Blueprint('api', __name__)

@api.route('/')
def index():
    return make_response(json.dumps({}))
