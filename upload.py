import ftplib
import os

def upload(ftp, file):
    print "Uploading ", file
    ext = os.path.splitext(file)[1]
    if ext in (".txt", ".htm", ".html"):
        ftp.storlines("STOR " + file, open(file))
    else:
        ftp.storbinary("STOR " + file, open(file, "rb"), 1024)

with open('/g/data/xc0/user/HatfieldDodds/_FTP_CREDENTIALS') as f:
    auth = f.read().split()

ftp = ftplib.FTP("ftp.wenfo.org")
ftp.login(*auth)
ftp.cwd('/public_html/apwm/latest')

os.chdir('/g/data1/ub8/apwm/APWM/latest/')

for filename in os.listdir('.'):
    upload(ftp, filename)

ftp.quit()
