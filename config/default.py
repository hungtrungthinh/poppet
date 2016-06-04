import os
from passlib.hash import sha256_crypt

#WTF
CSRF_ENABLED = True


#configure blue prints 

BLUEPRINTS = ('client','guest','admin','superadmin','analytics')



#Configure DB
basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)),'..','unifispot')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SECRET_KEY = 'once-a-cat-went-to-talk-asndksadmnkamndkamkda'

SECURITY_REGISTERABLE = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(os.path.abspath(os.path.dirname(__file__)),'database.db')
SECURITY_PASSWORD_HASH = 'sha256_crypt'
SECURITY_PASSWORD_SALT = "AJSHASJHAJSHASJHSAJHASJAHSJAHJSA"



#SQLALCHEMY_ECHO = True
STATIC_FILES = os.path.join(basedir,'static')

SITE_FILE_UPLOAD = 'uploads'
BASE_FOLDER = os.path.join(basedir,'static')

#SQLALCHEMY_ECHO = True
ASSETS_DEBUG = True 
DEBUG = False

DATA_INIT = False
NO_UNIFI = False

LOGIN_DISABLED = False

SECURITY_UNAUTHORIZED_VIEW = '/login'
SECURITY_POST_LOGIN_VIEW = '/'
SECURITY_POST_LOGOUT_VIEW = '/login'
SECURITY_RECOVERABLE = True

SECURITY_MSG_INVALID_PASSWORD = ("Bad username or password", "error")
SECURITY_MSG_PASSWORD_NOT_PROVIDED = ("Bad username or password", "error")
SECURITY_MSG_USER_DOES_NOT_EXIST = ("Bad username or password", "error")
SECURITY_EMAIL_SENDER = 'no-reply@unifispot.com'
SECURITY_TOKEN_MAX_AGE = 1800
SECURITY_TRACKABLE = True

TEMP_LOGIN_ENABLED = False
SMS_PREAUTH_ENABLED = False

MAIL_EXCEPTION_THROTTLE = 5


SQLALCHEMY_COMMIT_ON_TEARDOWN =False
CELERY_ALWAYS_EAGER = False
#http://primalpappachan.com/devops/2013/07/30/aws-rds--mysql-server-has-gone-away/
#--Fix for aws-rds-server has gone away
SQLALCHEMY_POOL_RECYCLE = 3600
REPORT_EMAIL_SENDER = 'no-reply@unifispot.com' 
ADMINS = []

#Flask-session configuration for server side session handling
#SESSION_TYPE = 'sqlalchemy'
#SESSION_COOKIE_DOMAIN ='unifispot.com'

SQLALCHEMY_TRACK_MODIFICATIONS = False
