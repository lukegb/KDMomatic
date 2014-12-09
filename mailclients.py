class BaseMailClient(object):
    def __init__(self, config):
        self.config = config
        self.initialize()

    def serialize_config(self):
        return self.config

    def retrieve_new_kdm_emails(self):
        return []

    def destroy(self):
        pass

class BaseMail(object):
    pass

    # This should have the following properties:
    # self.sender, self.subject

    # and the following methods:
    # self.mark_complete(), self.attachments()

class BaseAttachment(object):
    pass

    # This should have the following properties:
    # self.filename, self.content

class GmailAttachment(BaseAttachment):
    def __init__(self, client, message_id, part):
        self.client = client
        self.message_id = message_id
        self.part = part

    @property
    def filename(self):
        return self.part['filename']

    @property
    def content(self):
        if not self.part['body'].get('data') and self.part['body'].get('attachmentId'):
            attachment = self.client.gmail.users().messages().attachments().get(userId='me', messageId=self.message_id, id=self.part['body']['attachmentId']).execute()
            apart = attachment['data']
        else:
            apart = self.part['body']['data']
        from base64 import urlsafe_b64decode
        return urlsafe_b64decode(apart.encode('utf-8'))

class GmailMail(BaseMail):
    def __init__(self, client, message):
        self.client = client
        self.message = message

    def _get_headers(self, name):
        if 'payload' not in self.message:
            self.message = self._retrieve_full_message()
        return [x['value'] for x in self.message['payload']['headers'] if x['name'] == name]

    def _retrieve_full_message(self):
        return self.client.gmail.users().messages().get(userId='me', id=self.message['id']).execute()

    @property
    def sender(self):
        return self._get_headers('From')[0]

    @property
    def subject(self):
        return self._get_headers('Subject')[0]

    def attachments(self):
        attachments = []
        for part in self.message['payload']['parts']:
            if not part['filename']:
                continue

            attachments.append(GmailAttachment(self.client, self.message['id'], part))
        return attachments

    def mark_complete(self):
        self.client.gmail.users().messages().modify(userId='me', id=self.message['id'], body={'removeLabelIds': [], 'addLabelIds': [self.client.labels[self.client.KDM_DONE_LABEL]]}).execute()


class GmailMailClient(BaseMailClient):
    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]
    REDIRECT_DESTINATION = 'urn:ietf:wg:oauth:2.0:oob'
    KDM_QUERY = "label:digital-delivery has:attachment in:inbox -label:digital-delivery/kdmomatic"
    KDM_DONE_LABEL = "Digital Delivery/KDMomatic"

    def _store_credentials(self, user_id, credentials):
        self.config.setdefault('credentials', dict())[user_id] = credentials.to_json()
        self.config['last_user_id'] = user_id

    def _get_stored_credentials(self, user_id):
        from oauth2client.client import OAuth2Credentials
        creds = self.config.setdefault('credentials', dict()).get(user_id)
        if creds:
            creds = OAuth2Credentials.from_json(creds)
        return creds

    def _make_flow(self):
        from oauth2client.client import OAuth2WebServerFlow
        return OAuth2WebServerFlow(self.config['client_id'], self.config['client_secret'], ' '.join(self.OAUTH_SCOPES), redirect_uri=self.REDIRECT_DESTINATION)

    def _get_credentials(self, user_id):
        if user_id:
            credentials = self._get_stored_credentials(user_id)
            if credentials and credentials.refresh_token is not None:
                return credentials

        # we're going to have to do oauth...
        user_id = ''
        flow = self._make_flow()
        while True:
            authorization_url = flow.step1_get_authorize_url()
            print "I need to perform authentication. To continue, please visit\n\n{}\n\nand enter the code below:".format(authorization_url)
            try:
                auth_code = ''
                while not auth_code:
                    auth_code = raw_input("> ")
                credentials = flow.step2_exchange(auth_code)
                if credentials.refresh_token:
                    user_info = self._get_user_info(credentials)
                    user_id = user_info.get('id')
                    email_address = user_info.get('id')
                    self._store_credentials(user_id, credentials)
                    return credentials
                else:
                    print "Those credentials didn't come with a refresh token, for some reason."
                    print "Please try again."
                    continue
            except Exception, e:
                print "An error occurred during code exchange:", e
                print "Please try again."
                continue


    def _build_gmail_service(self, user_id=None):
        user_id = self.config.get('last_user_id')

        from apiclient.discovery import build
        import httplib2
        http = httplib2.Http()
        http = self._get_credentials(user_id).authorize(http)
        return build('gmail', 'v1', http=http)

    def _get_user_info(self, credentials):
        from apiclient.discovery import build
        import httplib2
        user_info_service = build(serviceName='oauth2', version='v2', http=credentials.authorize(httplib2.Http()))
        return user_info_service.userinfo().get().execute()

    def initialize(self):
        self.gmail = self._build_gmail_service()

        labels = self.gmail.users().labels().list(userId='me').execute()
        self.labels = {}
        for label in labels['labels']:
            self.labels[label['name']] = label['id']

    def retrieve_kdm_emails(self):
        next_page_token = None
        messages = []
        response = self.gmail.users().messages().list(q=self.KDM_QUERY, userId='me').execute()
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = self.gmail.users().messages().list(q=self.KDM_QUERY, userId='me', pageToken=page_token).execute()
            if 'messages' in response:
                messages.extend(response['messages'])
        return [GmailMail(self, message) for message in messages]
