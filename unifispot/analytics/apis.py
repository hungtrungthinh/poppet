from flask import jsonify,abort,request,current_app
from flask_security import current_user
from sqlalchemy.exc import IntegrityError
from flask_security import login_required,current_user,roles_accepted

from .models import Sitestat

import arrow
from unifispot.base.api import UnifispotAPI
from unifispot.extensions import db
from unifispot.base.utils.forms import print_errors,get_errors
from unifispot.client.models import Wifisite

from functools import wraps
from dateutil import tz
from sqlalchemy import and_,or_


class SitestatAPI(UnifispotAPI):

    ''' API class to deal with Site Daily status
    
    '''

    def __init__(self):
        super(self.__class__, self).__init__()
        self.columns = []
        self.entity_name = 'SitestatAPI'
        
    def get_modal_obj(self):
        return Sitestat()

    def get_form_obj(self):
        return None
      
    def datatable_obj(self,request,columns,index_column,db,modal_obj):
        return None

    def validate_url(f):
        #Validate that client is trying to view only the sites owned by him
        @wraps(f)
        def decorated_function(*args, **kwargs):
            id =  request.view_args.get('id')
            wifisite = None
            #perform additional permission checks
            if not  current_app.config['LOGIN_DISABLED']:                
                if id:
                    wifisite = Wifisite.query.filter_by(id=id).first()

                    if not wifisite:
                        current_app.logger.debug("Unknown Site ID: %s "%(request.url))
                        return jsonify({'status': 0,'msg':'Unknown Site ID'})
                    #client users have access only to sites owned by them
                    if current_user.type == 'client'  and  wifisite.client_id != current_user.id:
                        current_app.logger.debug("Client trying to access unauthorized URL %s "%(request.url))
                        return jsonify({'status': 0,'msg':'Not Authorized'})     
                    #admin users have access only to sites in their account  
                    if current_user.type == 'admin'  and  wifisite.account_id != current_user.account_id:
                        current_app.logger.debug("Admin trying to access unauthorized URL %s "%(request.url))
                        return jsonify({'status': 0,'msg':'Not Authorized'}) 

            kwargs['wifisite'] = wifisite
            return f(*args, **kwargs)
        return decorated_function

    @validate_url   
    def get(self,id,wifisite):   

        start = request.args.get('start')
        end   = request.args.get('end') 
        try:
            end_date    = arrow.get(end,'DD-MM-YYYY')
            start_date  = arrow.get(start,'DD-MM-YYYY')
        except:
            current_app.logger.exception('Exception while converting start/end dates in :%s'%request.url)
            end_date    = arrow.now() 
            start_date  = end_date.replace(days=-29)        
        if id:
            daystats = Sitestat.query.filter(and_(Sitestat.site_id==id,Sitestat.date>=start_date.floor('day').naive,
                    Sitestat.date<end_date.ceil('day').naive)).all()
            stats = Sitestat.get_dashboard_stats(daystats)
            return jsonify(stats)

        else:
            if current_user.type == 'client':
                daystats = Sitestat.query.outerjoin(Wifisite).filter(and_(Wifisite.account_id==current_user.account_id,Sitestat.date>=start_date.floor('day').naive,
                        Sitestat.date<end_date.ceil('day').naive)).all()
            else:
                daystats = Sitestat.query.outerjoin(Wifisite).filter(and_(Wifisite.account_id==current_user.account_id,Sitestat.date>=start_date.floor('day').naive,
                        Sitestat.date<end_date.ceil('day').naive)).all()
            stats = Sitestat.get_combine_stats(daystats)
            return jsonify(stats)

    @validate_url   
    def post(self,id,wifisite):   
        current_app.logger.debug("POST called on SitestatAPI  %s by :%s"%(request.url,current_user.id))  
        return jsonify({'status': 0,'msg':'Not Allowed'})

    @validate_url   
    def delete(self,id,wifisite):   
        current_app.logger.debug("Delete called on SitestatAPI  %s by :%s"%(request.url,current_user.id))  
        return jsonify({'status': 0,'msg':'Not Allowed'})
