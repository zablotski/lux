

class RestModel:
    '''Hold information about a model used for REST views

    .. attribute:: name

        name of this REST model

    .. attribute:: api_name

        name used as key in the dictionary of API endpoints. By default it is
        given by the plural of name + `_url`

    .. attribute:: form

        Form class for this REST model

    .. attribute:: editform

        Form class for this REST model in editing mode
    '''
    _columns = None
    _loaded = False

    def __init__(self, name, form=None, editform=None, columns=None,
                 url=None, api_name=None):
        self.name = name
        self.form = form
        self.editform = editform or form
        self.url = url or '%ss' % name
        self.api_name = '%s_url' % self.url
        self._columns = columns

    def tojson(self, obj, exclude=None, decoder=None):
        raise NotImplementedError

    def columns(self, app):
        '''Return a list fields describing the entries for a given model
        instance'''
        if not self._loaded:
            self._loaded = True
            self._columns = self._load_columns(app)
        return self._columns

    def get_target(self, request, id=None):
        '''Get a target for a form

        Used by HTML Router to get information about the LUX REST API
        of this Rest Model
        '''
        url = request.app.config.get('API_URL')
        if not url:
            return
        target = {'url': url, 'name': self.api_name}
        if id:
            target['id'] = id
        return target

    def _load_columns(self, app):
        return self._columns or []
