'''
This extension integrates pulsar-odm, an asynchronous object
data mapper built on top of pulsar.

It also implements an Admin inteface.

In order to use the Admin interface, the :setting:`ADMIN_URL`
needs to be specified.
'''
from pulsar import ImproperlyConfigured
from pulsar.apps.wsgi import WsgiHandler, wait_for_body_middleware
from pulsar.apps.greenio import WsgiGreen
from pulsar.utils.log import LocalMixin

import lux
from lux import Parameter
from lux.extensions.auth import RequirePermission

from .mapper import Mapper, model_iterator
from .green import GreenMapper
from .admin import Admin, AdminModel, adminMap
from .store import Store, RemoteStore, create_store, register_store, Command
from .api import CRUD
from .models import Model
from .backends import sql


class Extension(lux.Extension):
    '''Object data mapper extension
    '''
    _config = [
        Parameter('DATASTORE', None,
                  'Dictionary for mapping models to their back-ends database'),
        Parameter('SEARCHENGINE', None,
                  'Search engine for models'),
        Parameter('ADMIN_URL', None,
                  'Admin site url', True),
        Parameter('ADMIN_PERMISSIONS', 'admin',
                  'Admin permission name'),
        Parameter('GREEN_WSGI', 0,
                  'Run the WSGI handle in a pool of greenlet')]

    def on_config(self, app):
        app.mapper = AppMapper(app)

    def middleware(self, app):
        admin = app.config['ADMIN_URL']
        if admin:
            self.admin = admin = Admin(admin)
            for model in model_iterator(app.config['EXTENSIONS']):
                meta = model._meta
                admin_cls = adminMap.get(meta, AdminModel)
                if admin_cls:
                    admin.add_child(admin_cls(meta))
            permission = app.config['ADMIN_PERMISSIONS']
            return [RequirePermission(permission)(admin)]

    def on_loaded(self, app):
        '''Wraps the Wsgi handler into a greenlet friendly handler
        '''
        green = WsgiGreen(app.handler)
        self.logger.info('Setup green Wsgi handler')
        app.handler = WsgiHandler((wait_for_body_middleware, green),
                                  async=True)

    def on_html_document(self, app, request, doc):
        backend = request.cache.auth_backend
        permission = app.config['ADMIN_PERMISSIONS']
        if backend and not backend.has_permission(request, permission):
            doc.jscontext.pop('ADMIN_URL', None)


class AppMapper(LocalMixin):
    '''Lazy object data mapper.
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self):
        if not self.local.mapper:
            self.local.mapper = self._create_mapper()
        return self.local.mapper

    def clear(self):
        self.local.pop('mapper', None)

    def api_info(self, meta):
        '''Return a dictionary of information about the API for model meta.

        The best way to override this method is on your main application
        using the ``on_load`` callback.
        '''
        raise NotImplementedError

    def _create_mapper(self):
        datastore = self.app.config['DATASTORE']
        if not datastore:
            return
        elif isinstance(datastore, str):
            datastore = {'default': datastore}
        if 'default' not in datastore:
            raise ImproperlyConfigured('default datastore not specified')
        if self.app.config['GREEN_WSGI']:
            from .green import GreenMapper
            mapper = GreenMapper(datastore['default'])
        else:
            mapper = Mapper(datastore['default'])
        mapper.register_applications(self.app.config['EXTENSIONS'])
        return mapper


def database_create(app, dry_run=False):
    mapper = app.mapper()
    for manager in mapper:
        store = manager._store
        databases = yield from store.database_all()
        if store.database not in databases:
            if not dry_run:
                yield from store.database_create()
            app.write('Created database %s' % store)


def database_drop(app, dry_run=False):
    mapper = app.mapper()
    for manager in mapper:
        store = manager._store
        databases = yield from store.database_all()
        if store.database in databases:
            if not dry_run:
                yield from store.database_drop()
            app.write('Dropped database %s' % store)
