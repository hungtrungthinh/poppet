#! flask/bin/python
from os.path import abspath

from flask import current_app
from flask_script import Manager
from flask_assets import ManageAssets
from flask_migrate import Migrate, MigrateCommand

from unifispot import create_app
from unifispot.extensions import db,mail,celery,redis


app = create_app(mode= 'development')

app.run(host='0.0.0.0',debug = True)


