import os
import logging

from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.events import subscriber
from pyramid.events import ApplicationCreated
from pyramid.httpexceptions import HTTPFound
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from paste.httpserver import serve
import sqlite3

logging.basicConfig()
log = logging.getLogger(__file__)

here = os.path.dirname(os.path.abspath(__file__))

@subscriber(ApplicationCreated)
def application_created_subscriber(event):
    log.warn('Initializing database...')
    f = open(os.path.join(here, 'schema.sql'), 'r')
    stmt = f.read()
    settings = event.app.registry.settings
    db = sqlite3.connect(settings['db'])
    db.executescript(stmt)
    db.commit()
    f.close()

@subscriber(NewRequest)
def new_request_subscriber(event):
    request = event.request
    settings = request.registry.settings
    request.db = sqlite3.connect(settings['db'])
    request.add_finished_callback(close_db_connection)

@view_config(route_name='list', renderer='list.mako')
def list_view(request):
    rs = request.db.execute('select id, name from todos where closed = 0')
    todos = [dict(id=row[0], name=row[1]) for row in rs.fetchall()]
    return {'todos': todos}

@view_config(route_name='new', renderer='new.mako')
def new_view(request):
    if request.method == 'POST':
        if request.POST.get('name'):
            request.db.execute('insert into todos (name, closed) values (?, ?)',
                               [request.POST['name'], 0])
            request.db.commit()
            request.session.flash('New todo was successfully added!')
            return HTTPFound(location=request.route_url('list'))
        else:
            request.session.flash('Please enter a name for the todo!')
    return {}

@view_config(route_name='close')
def close_view(request):
    todo_id = int(request.matchdict['id'])
    request.db.execute('update todos set closed = ? where id = ?', (1, todo_id))
    request.db.commit()
    request.session.flash('Todo was successfully closed.')
    return HTTPFound(location=request.route_url('list'))

@view_config(context='pyramid.exceptions.NotFound',
             renderer='notfound.mako')
def notfound_view(self):
    return {}

def close_db_connection(request):
    request.db.close()

if __name__ == '__main__':
    # configuration settings
    settings = {}
    settings['reload_all'] = True
    settings['debug_all'] = True
    settings['db'] = os.path.join(here, 'todo.db')
    settings['mako.directories'] = os.path.join(here, 'templates')

    session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')

    config = Configurator(settings=settings, session_factory=session_factory)
    config.add_route('list', '/')
    config.add_route('new', '/new')
    config.add_route('close', '/close/{id}')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.scan()

    app = config.make_wsgi_app()
    serve(app, host='0.0.0.0')
