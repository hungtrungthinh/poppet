BUILDDIR=build
SOURCEDIR=poppet
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

git clone https://rakeshmmk@bitbucket.org/rakeshmmk/poppet.git

rm -rf $SOURCEDIR/.git



echo "-----------------------------Building Packages-----------------------------"
cd build 
fpm -s dir -t deb -n poppet -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,upstart,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev,tcl8.6-dev,tk8.6-dev,python-tk" \
    --after-install ../poppet/scripts/postinst -a i686 \
    --deb-templates ../poppet/scripts/templates \
    --deb-config ../poppet/scripts/config \
    ../poppet/=/usr/share/nginx/poppet 
fpm -s dir -t deb -n poppet -v $BUILDVER -d "nginx,redis-server,mysql-server,mysql-client,python-dev,python,libmysqlclient-dev,python-pip,git,libffi-dev,upstart,supervisor,libssl-dev,libtiff5-dev,libjpeg8-dev,zlib1g-dev,libfreetype6-dev,liblcms2-dev,libwebp-dev,tcl8.6-dev,tk8.6-dev,python-tk" \
    --after-install ../poppet/scripts/postinst -a amd64\
    --deb-templates ../poppet/scripts/templates \
    --deb-config ../poppet/scripts/config \
         ../poppet/=/usr/share/nginx/poppet 
tar -zcvf poppet-$BUILDVER.tar.gz poppet

cp /home/build/poppet_$BUILDVER'_amd64.deb' /usr/share/nginx/download.poppet.com/latest_amd64.deb
cp /home/build/poppet_$BUILDVER'_i686.deb' /usr/share/nginx/download.poppet.com/latest_i686.deb
cp /home/build/poppet_$BUILDVER'_amd64.deb' /usr/share/nginx/download.poppet.com/
cp /home/build/poppet_$BUILDVER'_i686.deb' /usr/share/nginx/download.poppet.com/
