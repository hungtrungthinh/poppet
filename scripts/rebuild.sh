cd ..
echo "---delete all files and folders----"
rm -rf migrations 

mysqladmin -uroot -p drop unifispot

mysql -u root -p -e "create database unifispot"; 
echo "-----Initialize all DBs------------"
python manage.py db init
python manage.py db migrate
python manage.py db upgrade


