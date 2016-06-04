CONFFILE=/usr/share/nginx/unifispot/instance/config.py

apt-get update
apt-get install nginx redis-server mysql-server mysql-client python-dev libmysqlclient-dev python-pip git libffi-dev -y 


cd /usr/share/nginx
echo "------------------------------Getting latest Source files----------------------------"

if [  -d unifispot ]; then
    cd unifispot
    git pull
else 
    git clone https://rakeshmmk@bitbucket.org/rakeshmmk/unifispot.git
    cd unifispot
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
mkdir -p unifispot/static/uploads/


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
    echo " Trying to create a new Db named unifispot"
    mysql -u $username -p$passwd -e "create database unifispot";
    sed -i "s/^SQLALCHEMY_DATABASE_URI.*/SQLALCHEMY_DATABASE_URI=\"mysql:\/\/$username:$passwd@$host\/unifispot\"/g"  $CONFFILE
fi

.env/bin/python manage.py db migrate
.env/bin/python manage.py db upgrade
.env/bin/python manage.py init_data

#configure UWSGI
mkdir -p /etc/uwsgi
mkdir -p /etc/uwsgi/vassals
rm -rf /etc/uwsgi/vassals/uwsgi.ini
ln -s /usr/share/nginx/unifispot/scripts/uwsgi.ini /etc/uwsgi/vassals/uwsgi.ini
chown -R www-data:www-data /usr/share/nginx/unifispot
cp uwsgi.conf /etc/init/

#configure Nginx
rm -rf /etc/nginx/sites-enabled/default
cp scripts/wifiapp.conf /etc/nginx/sites-available/wifiapp.conf
ln -s /etc/nginx/sites-available/wifiapp.conf /etc/nginx/sites-enabled/wifiapp

service uwsgi restart
service nginx restart

#configure celery
apt-get install supervisor
rm -f  /etc/supervisor/conf.d/unifispot_celery.conf
ln -s /usr/share/nginx/unifispot/scripts/supervisord.conf  /etc/supervisor/conf.d/unifispot_celery.conf
service supervisor restart