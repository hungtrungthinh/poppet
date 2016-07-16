CONFFILE=/usr/share/nginx/poppet/instance/config.py

apt-get update
apt-get install nginx redis-server mysql-server mysql-client python-dev python libmysqlclient-dev python-pip git libffi-dev  supervisor libssl-dev libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev -y


cd /usr/share/nginx
echo "------------------------------Getting latest Source files----------------------------"

if [  -d poppet ]; then
    cd poppet
    git pull
else 
   https://github.com/unifispot/poppet.git
    cd poppet
fi


echo "------------------------------Create new venv and activate----------------------------"
pip install virtualenv
virtualenv .env
source .env/bin/activate

echo "------------------------------Install all dependencies----------------------------"
pip install -r requirements.txt
mkdir -p instance
mkdir -p logs
mkdir -p touch instance/__init__.py
mkdir -p poppet/unifispot/static/uploads/


if [ ! -d migrations ]; then
    cp scripts/instance_sample.py instance/config.py 
    .env/bin/python manage.py db init

fi

#Check if DB is properly configured
if  ! .env/bin/python manage.py db current >/dev/null 2>/dev/null  ; then 

    read -p "Please Enter your MySQL Host name [localhost]: " host
    host=${host:-localhost}
    read -p "Please Enter your MySQL Root Username [root]: " username
    username=${username:-root}
    echo "Please Enter your MySQL Root Password []: "
    read -s  passwd
    echo " Trying to create a new Db named poppet"
    mysql -u $username -p$passwd -e "create database poppet";
    sed -i "s/^SQLALCHEMY_DATABASE_URI.*/SQLALCHEMY_DATABASE_URI=\"mysql:\/\/$username:$passwd@$host\/poppet\"/g"  $CONFFILE
fi

.env/bin/python manage.py db migrate
.env/bin/python manage.py db upgrade
.env/bin/python manage.py init_data
.env/bin/python manage.py rebuild_daily_stat
.env/bin/python manage.py migrate_vouchers
.env/bin/python manage.py set_unifiport

if [  -d /etc/init/uwsgi.conf ]; then
    echo '-------------Upstart UWSGI config found, removing and upgrading to supervisor--------------'
    if service --status-all | grep -Fq 'uwsgi'; then
      sudo service uwsgi stop
    fi
    rm -rf /etc/init/uwsgi.conf

fi

if [ ! -d /etc/uwsgi ]; then
    echo '-------------------------Creating /etc/uwsgi-----------------------------------------'
    mkdir /etc/uwsgi

fi
if [ ! -d /etc/uwsgi/vassals ]; then
    echo '-------------------------Creating /etc/uwsgi/vassals-----------------------------------------'        
    mkdir /etc/uwsgi/vassals
    ln -sf /usr/share/nginx/poppet/scripts/uwsgi.ini /etc/uwsgi/vassals/uwsgi.ini

fi

if [ ! -f /etc/uwsgi/vassals/uwsgi.ini ]; then
    echo '-------------------------Configuring /etc/uwsgi/vassals/uwsgi.ini-----------------------------'
    ln -sf /usr/share/nginx/poppet/scripts/uwsgi.ini /etc/uwsgi/vassals/uwsgi.ini

fi
if [ ! -f /etc/nginx/sites-enabled/wifiapp ]; then
    echo '-------------------------Configuring nGINX-----------------------------------------'
    rm -rf /etc/nginx/sites-enabled/default
    cp /usr/share/nginx/poppet/scripts/wifiapp.conf /etc/nginx/sites-available/wifiapp.conf
    ln -sf /etc/nginx/sites-available/wifiapp.conf /etc/nginx/sites-enabled/wifiapp
fi

if [ ! -f /etc/supervisor/conf.d/unifispot_celery.conf ]; then
    echo '-------------------------Configuring celeryd-----------------------------------------'
    ln -sf /usr/share/nginx/poppet/scripts/supervisord.conf  /etc/supervisor/conf.d/unifispot_celery.conf
fi

chown -R www-data:www-data /usr/share/nginx/poppet
service nginx restart
service supervisor restart
