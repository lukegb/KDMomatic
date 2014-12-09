try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import zipfile
import posixpath

class KDM(object):
    def __init__(self, filename, xml):
        self.filename = filename
        self.xml = xml

    def as_file(self):
        return StringIO.StringIO(self.xml)

def xml_to_kdms(filename, content):
    yield KDM(filename, content)

def zip_to_kdms(zipcontent):
    zipio = StringIO.StringIO(zipcontent)
    with zipfile.ZipFile(zipio, 'r') as zipf:
        kdmfns = [kdm for kdm in zipf.namelist() if kdm.lower().endswith('.xml') or kdm.lower().endswith('.kdm')]
        for kdmfn in kdmfns:
            yield next(xml_to_kdms(posixpath.basename(kdmfn), zipf.read(kdmfn)))

def attachment_to_kdms(attachment):
    fn = attachment.filename.lower()
    if fn.endswith('.xml') or fn.endswith('.kdm'):
        return xml_to_kdm(attachment.filename, attachment.content)
    elif fn.endswith('.zip'):
        return zip_to_kdms(attachment.content)
