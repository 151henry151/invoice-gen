from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app import app

# Create a simple WSGI application for the root path
def empty_app(environ, start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']

# Create the application instance with both root and /invoice paths
application = DispatcherMiddleware(empty_app, {
    '/invoice': app
})

if __name__ == '__main__':
    application.run() 