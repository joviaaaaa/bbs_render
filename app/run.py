from flask import Blueprint, Flask, request, render_template, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask import jsonify
import ipwhois
import hashlib
from flask import Markup
from ipwhois import IPWhois

#from bbs.common.utility import err_response
from bbs.models import db
from bbs.views.bbs import bbs 

import os
import re

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

app.register_blueprint(bbs)

with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5050)
