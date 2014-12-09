from mailclients import GmailMailClient
from kdmclients import FTPKDMClient
from kdmtransformer import attachment_to_kdms

config = {
    'gmail': {
        'client_id': 'GMAIL_CLIENTID',
        'client_secret': 'GMAIL_CLIENTSECRET',
    },
    'ftp': {
        'destination': 'FTP_HOSTNAME',
        'username': 'FTP_USERNAME',
        'password': 'FTP_PASSWORD',
    },
}
import os.path, json
if not os.path.exists('config.json'):
    with open('config.json', 'w') as f:
        json.dump(config, f)
else:
    with open('config.json', 'r') as f:
        config = json.load(f)

x = GmailMailClient(config['gmail'])
y = FTPKDMClient(config['ftp']) 
try:
    for email in x.retrieve_kdm_emails():
        print "EMAIL:", email.sender, email.subject
        for attachment in email.attachments():
            print "\t", attachment.filename
            for kdm in attachment_to_kdms(attachment):
                print "\t\t", kdm.filename
                y.upload_kdm(kdm)
        email.mark_complete()
finally:
    x.destroy()
    y.destroy()
    
    config['gmail'] = x.serialize_config()
    config['ftp'] = y.serialize_config()
    with open('config.json', 'w') as f:
        json.dump(config, f)
