import ConfigParser

class Config():

    def __init__(self, filename):
        config = ConfigParser.ConfigParser()
        config.read(filename)

        class BunchOParams:
            pass

        # main
        self.main = BunchOParams()
        self.main.instance_string = config.get('main', 'instance_string')
        self.main.secure_cookie = config.getboolean('main', 'secure_cookie')
        self.main.session_lifetime = config.getint('main', 'session_lifetime')
        self.main.secret_key = config.get('main', 'secret_key')
        self.main.url = config.get('main', 'url')
        self.main.debug = config.getboolean('main', 'debug')
        self.main.db_connection = config.get('main', 'db_connection')
        self.main.paginate_row_count = config.getint('main', 'paginate_row_count')

        # email
        self.email = BunchOParams()
        self.email.from_ = config.get('email', 'from')
        self.email.smtp = config.get('email', 'smtp')
        self.email.use_auth = config.getboolean('email', 'use_auth')
        self.email.user = config.get('email', 'user')
        self.email.password = config.get('email', 'password')
        self.email.use_mandrill = config.getboolean('email', 'use_mandrill')
        self.email.mandrill_api_key = config.get('email', 'mandrill_api_key')
