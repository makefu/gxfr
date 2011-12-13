#!/usr/bin/python -tt

# send yourself an email through gmail from stdin
# used for crontab alerts
# can easily be modified to send mail to other places
# usage: echo test | ./mail.py username 'P@$$w0rd'

import smtplib, sys
from email.mime.text import MIMEText

# gmail credentials
username = sys.argv[1].split('@')[0]
password = sys.argv[2]

# create a text/plain message
msg = MIMEText(sys.stdin.read())

# set message variables
me = 'Crontab'
you = '%s@gmail.com' % (username)
msg['Subject'] = 'Daily Denies'
msg['From'] = me
msg['To'] = you

# send message
s = smtplib.SMTP('smtp.gmail.com:587')
s.ehlo()
s.starttls()
s.ehlo()
s.login(username, password)
s.sendmail(me, [you], msg.as_string())
print 'Message successfully sent to %s.' % (you)
s.quit()
