from inyoka.core.routing import href
from inyoka.core.auth import AuthSystemBase, User
from inyoka.core.http import redirect

class EasyAuth(AuthSystemBase):
    _store = {}

    def perform_login(self, request, username, password):
        user = User(username, username, username)
        self.set_user(request, user)
        self._store[user.id] = user
        return redirect(href('portal/index'))

    def get_user(self, request):
        return self._store.get(request.session.get('user_id'))
