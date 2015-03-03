import lux
from lux import route, Router as WebRouter
from lux.forms import Form

from pulsar import Http404, PermissionDenied, HttpRedirect, MethodNotAllowed
from pulsar.apps.wsgi import Json, Router

from .forms import (LoginForm, CreateUserForm, ChangePasswordForm,
                    ForgotPasswordForm, PasswordForm)
from .backend import AuthenticationError
from .jwtmixin import jwt


__all__ = ['Login', 'SignUp', 'Logout', 'Token', 'ForgotPassword',
           'ChangePassword', 'csrf', 'RequirePermission']


def csrf(method):
    '''Decorator which makes sure the CSRF token is checked

    This decorator should be applied to all view handling POST data
    without using a :class:`.Form`.
    '''
    def _(self, request):
        # make sure CSRF is checked
        data, files = request.data_and_files()
        Form(request, data=data, files=files)
        return method(self, request)

    return _


class FormMixin(object):
    default_form = Form
    form = None
    redirect_to = None

    @property
    def fclass(self):
        return self.form or self.default_form

    def maybe_redirect_to(self, request, form, **kw):
        redirect_to = self.redirect_url(request)
        if redirect_to:
            return Json({'success': True,
                         'redirect': redirect_to}
                        ).http_response(request)
        else:
            return Json(form.tojson()).http_response(request)

    def redirect_url(self, request):
        redirect_to = self.redirect_to
        if hasattr(redirect_to, '__call__'):
            redirect_to = redirect_to(request, **kw)
        if redirect_to:
            return request.absolute_uri(redirect_to)


class WebFormRouter(WebRouter, FormMixin):
    uirouter = False
    template = None

    def get_html(self, request):
        '''Handle the HTML page for login
        '''
        form = self.fclass(request).layout
        html = form.as_form(action=request.full_path(),
                            enctype='multipart/form-data',
                            method='post')
        context = {'form': html.render(request)}
        return request.app.render_template(self.template, context,
                                           request=request)


class Login(WebFormRouter):
    '''Adds login get ("text/html") and post handlers
    '''
    default_form = LoginForm
    template = 'login.html'
    redirect_to = '/'

    def get(self, request):
        if request.cache.user.is_authenticated():
            raise HttpRedirect(self.redirect_to)
        return super().get(request)

    def post(self, request):
        '''Handle login post data
        '''
        user = request.cache.user
        if user.is_authenticated():
            raise MethodNotAllowed
        form = self.fclass(request, data=request.body_data())
        if form.is_valid():
            auth = request.cache.auth_backend
            try:
                user = auth.authenticate(request, **form.cleaned_data)
                auth.login(request, user)
            except AuthenticationError as e:
                form.add_error_message(str(e))
            else:
                return self.maybe_redirect_to(request, form, user=user)
        return Json(form.tojson()).http_response(request)


class SignUp(WebFormRouter):
    template = 'signup.html'
    default_form = CreateUserForm
    redirect_to = '/'

    def post(self, request):
        '''Handle login post data
        '''
        user = request.cache.user
        if user.is_authenticated():
            raise MethodNotAllowed
        data = request.body_data()
        form = self.fclass(request, data=data)
        if form.is_valid():
            data = form.cleaned_data
            auth_backend = request.cache.auth_backend
            try:
                user = auth_backend.create_user(request, **data)
            except AuthenticationError as e:
                form.add_error_message(str(e))
            else:
                return self.maybe_redirect_to(request, form, user=user)
        return Json(form.tojson()).http_response(request)

    @route('confirmation/<username>')
    def new_confirmation(self, request):
        username = request.urlargs['username']
        backend = request.cache.auth_backend
        user = backend.confirm_registration(request, username=username)
        raise HttpRedirect(self.redirect_url(request))

    @route('<key>')
    def confirmation(self, request):
        key = request.urlargs['key']
        backend = request.cache.auth_backend
        user = backend.confirm_registration(request, key)
        raise HttpRedirect(self.redirect_url(request))


class ChangePassword(WebFormRouter):
    default_form = ChangePasswordForm

    def post(self, request):
        '''Handle post data
        '''
        user = request.cache.user
        if not user.is_authenticated():
            raise MethodNotAllowed
        form = self.fclass(request, data=request.body_data())
        if form.is_valid():
            auth = request.cache.auth_backend
            password = form.cleaned_data['password']
            auth.set_password(user, password)
            return self.maybe_redirect_to(request, form, user=user)
        return Json(form.tojson()).http_response(request)


class ForgotPassword(WebFormRouter):
    '''Adds login get ("text/html") and post handlers
    '''
    default_form = ForgotPasswordForm
    template = 'forgot.html'
    reset_template = 'reset_password.html'

    def post(self, request):
        '''Handle request for resetting password
        '''
        user = request.cache.user
        if user.is_authenticated():
            raise MethodNotAllowed
        form = self.fclass(request, data=request.body_data())
        if form.is_valid():
            auth = request.cache.auth_backend
            email = form.cleaned_data['email']
            try:
                auth.password_recovery(request, email)
            except AuthenticationError as e:
                form.add_error_message(str(e))
            else:
                return self.maybe_redirect_to(request, form, user=user)
        return Json(form.tojson()).http_response(request)

    @route('<key>')
    def get_reset_form(self, request):
        key = request.urlargs['key']
        try:
            user = request.cache.auth_backend.get_user(request, auth_key=key)
        except AuthenticationError as e:
            session = request.cache.session
            session.error('The link is no longer valid, %s' % e)
            return request.redirect('/')
        if not user:
            raise Http404
        form = PasswordForm(request).layout
        html = form.as_form(action=request.full_path('reset'),
                            enctype='multipart/form-data',
                            method='post')
        context = {'form': html.render(request),
                   'site_name': request.config['APP_NAME']}
        return request.app.render_template(self.reset_template, context,
                                           request=request)

    @route('<key>/reset', method='post',
           response_content_types=lux.JSON_CONTENT_TYPES)
    def reset(self, request):
        key = request.urlargs['key']
        session = request.cache.session
        result = {}
        try:
            user = request.cache.auth_backend.get_user(request, auth_key=key)
        except AuthenticationError as e:
            session.error('The link is no longer valid, %s' % e)
        else:
            if not user:
                session.error('Could not find the user')
            else:
                form = PasswordForm(request, data=request.body_data())
                if form.is_valid():
                    auth = request.cache.auth_backend
                    password = form.cleaned_data['password']
                    auth.set_password(user, password)
                    session.info('Password successfully changed')
                    auth.auth_key_used(key)
                else:
                    result = form.tojson()
        return Json(result).http_response(request)


class Logout(Router, FormMixin):
    '''Logout handler, post view only
    '''
    redirect_to = '/'

    def post(self, request):
        '''Logout via post method
        '''
        # validate CSRF
        form = self.fclass(request, data=request.body_data())
        backend = request.cache.auth_backend
        backend.logout(request)
        return self.maybe_redirect_to(request, form)


class Token(Router):

    @csrf
    def post(self, request):
        '''Obtain a Json Web Token (JWT)
        '''
        user = request.cache.user
        if not user:
            raise PermissionDenied
        cfg = request.config
        secret = cfg['SECRET_KEY']
        token = jwt.encode({'username': user.username,
                            'application': cfg['APP_NAME']}, secret)
        return Json({'token': token}).http_response(request)


class RequirePermission(object):
    '''Decorator to apply to a view
    '''
    def __init__(self, name):
        self.name = name

    def __call__(self, callable):

        def _(*args, **kw):
            return callable(*args, **kw)

        return _
