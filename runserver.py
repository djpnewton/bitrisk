#!/usr/bin/python

from bitrisk import app

import os
host = os.getenv('HOST', '127.0.0.1')
port = int(os.getenv('PORT', 5000))

# get filenames before daemonizing
app_log_filename = os.path.realpath('log/bitrisk.log')
access_log_filename = os.path.realpath('log/access.log')

def log_app():
    import cherrypy
    from paste.translogger import TransLogger
    import logging
    from logging.handlers import RotatingFileHandler
    # Enable app/error logging
    handler = RotatingFileHandler(app_log_filename, maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    cherrypy.log.error_file = ''
    cherrypy.log.error_log.addHandler(handler)
    # Enable WSGI access logging access via Paste
    app_logged = TransLogger(app)
    handler = RotatingFileHandler(access_log_filename, maxBytes=10000000, backupCount=5)
    logger = logging.getLogger('wsgi')
    logger.addHandler(handler)
    cherrypy.log.access_file = ''

    return app_logged

def start_cherrypy():
    import cherrypy
    # create cherrypy logged app
    app_logged = log_app()
    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app_logged, '/')
    # Set the configuration of the web server
    cherrypy.config.update({
        'engine.autoreload.on': True,
        'log.screen': True,
        'server.socket_host': host,
        'server.socket_port': port,
        # Do not just listen on localhost
        'server.socket_host': '0.0.0.0'
    })
    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()

def start_debug():
    app.debug = True
    app.run(host, port)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2 and 'debug' == sys.argv[1]:
        start_debug()
    else:
        from bitrisk.daemon import Daemon
        class BitriskDaemon(Daemon):
            def run(self):
                start_cherrypy()
        daemon = BitriskDaemon('/tmp/bitrisk-daemon.pid')
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                daemon.start()
            elif 'stop' == sys.argv[1]:
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
            elif 'foreground' == sys.argv[1]:
                daemon.run()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(0)

        else:
            print "usage: %s start|stop|restart|foreground|debug" % sys.argv[0]
            sys.exit(2)
