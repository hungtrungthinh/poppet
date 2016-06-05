1. Install nginx and Redis

    ```sh
    sudo apt-get update
    sudo apt-get install nginx redis-server -y
    ```

2. Install MySQL Server and configure username/password

    ```sh
    sudo apt-get install mysql-server mysql-client -y
    ```

3. Create required database


    ```sh
    mysql -u root -p -e "create database poppet";
    ```

3. Install dependencies

    ```sh
    sudo apt-get install nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,upstart,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev,tcl8.6-dev,tk8.6-dev,python-tk,upstart -y
    sudo pip install -U pip
    ```

4. Download latest version of poppet and install

    ```sh
    cd /usr/share/nginx/
    git clone https://github.com/unifispot/poppet.git
    cd poppet
    mkdir -p instance
    touch instance/__init__.py
    cp instance_sample.py instance/config.py
    mkdir -p unifispot/static/uploads/
    pip install virtualenv
    virtualenv .env
    mkdir -p logs
    source .env/bin/activate
    pip install -r requirements.txt
    ```

5. Configure Settings, by opening `/usr/share/nginx/poppet/instance/config.py`

    Mainly edit `SQLALCHEMY_DATABASE_URI` with correct MySQL settings

6. Create all the required DB entries

    ```sh
    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade
    python manage.py init_data
    ```

7. Configure uWSGI and Nginx

    ```sh
    mkdir -p /var/log/uwsgi
    chown -R www-data:www-data /var/log/uwsgi
    mkdir -p /etc/uwsgi
    mkdir -p /etc/uwsgi/vassals
    rm -rf /etc/uwsgi/vassals/uwsgi.ini
    ln -s /usr/share/nginx/poppet/script/uwsgi.ini /etc/uwsgi/vassals/uwsgi.ini
    chown -R www-data:www-data /usr/share/nginx/poppet
    chown -R www-data:www-data /var/log/uwsgi/
    cp script/uwsgi.conf /etc/init/
    rm -rf /etc/nginx/sites-enabled/default
    cp script/wifiapp.conf /etc/nginx/sites-available/wifiapp.conf
    ln -s /etc/nginx/sites-available/wifiapp.conf /etc/nginx/sites-enabled/wifiapp
    rm /etc/nginx/sites-enabled/default
    ```

8. Restart Nginx and uWSGI

    ```sh
    service nginx restart
    service uwsgi restart
    ```

9. Install Iptables persistant

    ```sh
    apt-get install iptables-persistent --yes --force-yes
    ```


10. Configure Iptables and save the rules

    ```sh
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    iptables -I INPUT 1 -i lo -j ACCEPT
    iptables -A INPUT -p tcp --dport 8081 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8880 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8843 -j ACCEPT
    iptables -A INPUT -p tcp --dport 27117 -j ACCEPT
    iptables -A INPUT -j DROP
    invoke-rc.d iptables-persistent save
    ```

11. That's it!! If everything is fine you should be able to see login page when you browse http://<your server ip>