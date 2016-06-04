''' Tests for admin.models '''

import sys
import pytest
from flask import current_app
from sqlalchemy import and_,or_

from unifispot.guest.models import Guest,Device,Guestsession,Guesttrack
from unifispot.admin.models import Admin
from unifispot.superadmin.models import Notification,Account
from unifispot.models import db
import time,uuid

from unifispot.const import *

@pytest.fixture(scope='function')
def populate_notifications():
    #add random notifications
    pass
    


