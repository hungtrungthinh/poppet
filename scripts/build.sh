BUILDDIR=build
SOURCEDIR=unifispot
BUILDVER=1.1.0

if [ -d "$SOURCEDIR" ]; then
    printf '%s\n' "Removing SOURCEDIR  ($SOURCEDIR)"
    rm -rf "$SOURCEDIR"
fi

if [ -d "$BUILDDIR" ]; then
    printf '%s\n' "Removing BUILDDIR  ($BUILDDIR)"
    rm -rf "$BUILDDIR"
fi
mkdir "$BUILDDIR"
mkdir "$SOURCEDIR"

git clone https://rakeshmmk@bitbucket.org/rakeshmmk/unifispot.git

rm -rf $SOURCEDIR/.git



echo "-----------------------------Building Packages-----------------------------"
cd build 
fpm -s dir -t deb -n unifispot -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,upstart,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev,tcl8.6-dev,tk8.6-dev,python-tk" \
    --after-install ../unifispot/scripts/postinst -a i686 \
    --deb-templates ../unifispot/scripts/templates \
    --deb-config ../unifispot/scripts/config \
    ../unifispot/=/usr/share/nginx/unifispot 
fpm -s dir -t deb -n unifispot -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,upstart,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev,tcl8.6-dev,tk8.6-dev,python-tk" \
    --after-install ../unifispot/scripts/postinst -a amd64\
    --deb-templates ../unifispot/scripts/templates \
    --deb-config ../unifispot/scripts/config \
         ../unifispot/=/usr/share/nginx/unifispot 
tar -zcvf unifispot-$BUILDVER.tar.gz unifispot

cp /home/build/unifispot_$BUILDVER'_amd64.deb' /usr/share/nginx/download.unifispot.com/latest_amd64.deb
cp /home/build/unifispot_$BUILDVER'_i686.deb' /usr/share/nginx/download.unifispot.com/latest_i686.deb
cp /home/build/unifispot_$BUILDVER'_amd64.deb' /usr/share/nginx/download.unifispot.com/
cp /home/build/unifispot_$BUILDVER'_i686.deb' /usr/share/nginx/download.unifispot.com/
