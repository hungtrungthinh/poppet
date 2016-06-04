#!/usr/bin/python
import sys
import os

siteid = sys.argv[1]
url = sys.argv[2]

if not siteid or not url:
    print 'Usage ./deploy.py <sitedid> <url>'

filename = '/var/lib/unifi/sites/%s/portal/index.html'%siteid

html='''<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="1;url=http://%s/guest/s/%s/?ap=<unifi var="ap_mac" />&id=<unifi var="mac" />&ssid=<unifi var="ssid" />">
        <script type="text/javascript">
            window.location.href = "http://%s/guest/s/%s/?ap=<unifi var="ap_mac" />&id=<unifi var="mac" />&ssid=<unifi var="ssid" />"
        </script>
        <title>Page Redirection</title>
    </head>
    <body>
        <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
        If you are not redirected automatically, follow the <a href='http://%s/guest/s/%s/?ap=<unifi var="ap_mac" />&id=<unifi var="mac" />&ssid=<unifi var="ssid" />'>click</a>
    </body>
</html>'''%(url,siteid,url,siteid,url,siteid)


os.remove(filename)


with open(filename,'w') as output:
    output.write(html)

