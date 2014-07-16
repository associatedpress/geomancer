from flask import Blueprint, make_response, request, session, render_template
import json

api = Blueprint('api', __name__)

@api.route('/')
def index():
    return render_template('index.html')
