import scrapelib
from urllib import urlencode
import json
import os
from geo.utils.mancer import Mancer
from geo.utils.helpers import encoded_dict
from string import punctuation
import re

class USASpendingError(Exception):
    def __init__(self, message, body=None):
        Exception.__init__(self, message)
        self.message = message
        self.body = body

class USASpending(Mancer):
    """ 
    Subclassing Mancer
    """
    
    def geo_lookup(self, search_term, geo_type=None):
        """ 
        May not need this
        """
        pass

    def search(self, geo_ids=None, columns=None):
        """
        Yay!
        """
        pass
