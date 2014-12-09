class BaseKDMClient(object):
    def __init__(self, config):
        self.config = config
        self.initialize()

    def serialize_config(self):
        return self.config

    def upload_kdm(self, kdm):
        pass

    def destroy(self):
        pass

class FTPKDMClient(BaseKDMClient):
    def initialize(self):
        import ftplib
        self.ftp = f = ftplib.FTP(self.config['destination'])
        f.login(self.config['username'], self.config['password'])
        if self.config.get('subdir'):
            f.cwd(self.config['subdir'])

    def upload_kdm(self, kdm):
        kdmf = kdm.as_file()
        self.ftp.storbinary('STOR {}'.format(kdm.filename), kdmf)

    def destroy(self):
        self.ftp.quit()
