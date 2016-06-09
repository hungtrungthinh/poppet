BUILDDIR=build
SOURCEDIR=poppet



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

git clone https://github.com/unifispot/poppet.git

rm -rf $SOURCEDIR/.git

. $SOURCEDIR/unifispot/version.py

BUILDVER=$version

echo "-----------------------------Building Packages-----------------------------"
cd $BUILDDIR 
fpm -s dir -t deb -n poppet -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev" \
    --after-install ../poppet/scripts/postinst -a i686 \
    --deb-templates ../poppet/scripts/templates \
    --deb-config ../poppet/scripts/config \
    ../poppet/=/usr/share/nginx/poppet 
fpm -s dir -t deb -n poppet -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev" \
    --after-install ../poppet/scripts/postinst -a amd64\
    --deb-templates ../poppet/scripts/templates \
    --deb-config ../poppet/scripts/config \
         ../poppet/=/usr/share/nginx/poppet 
tar -zcvf poppet-$BUILDVER.tar.gz poppet

cp /home/$BUILDDIR/poppet_$BUILDVER'_amd64.deb' /usr/share/nginx/download.unifispot.com/latest_amd64.deb
cp /home/$BUILDDIR/poppet_$BUILDVER'_i686.deb' /usr/share/nginx/download.unifispot.com/latest_i686.deb
cp /home/$BUILDDIR/poppet_$BUILDVER'_amd64.deb' /usr/share/nginx/download.unifispot.com/
cp /home/$BUILDDIR/poppet_$BUILDVER'_i686.deb' /usr/share/nginx/download.unifispot.com/
