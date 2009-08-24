from werkzeug.routing import Submount, EndpointPrefix
from inyoka import Component

class Controller(Component):
    # The prefix, will get prefix.domain, or domain/prefix
    # depending on the config.
    url_section = ''

    # The url objects, without Subdomain or Endpointprefix,
    # inyoka takes care of it.
    url_rules = []

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}

        urls = []

        for comp in cls.get_components():
            url_map = {}
            for method in dir(comp):
                try:
                    method = getattr(comp, method)
                    endpoint_name = getattr(method, 'endpoint')
                    url_map[endpoint_name] = method
                except AttributeError:
                    continue

            urls.append(Submount('/%s' % comp.url_section,
                             [EndpointPrefix('%s/' % comp.url_section,
                                             comp.url_rules)]
                        ))
            cls._endpoint_map.setdefault(comp.url_section, {}).update(url_map)
        
        return urls

    @classmethod
    def get_view(cls, endpoint):
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

def register(endpoint_name):
    def wrap(func):
        func.endpoint = endpoint_name
        return func
    return wrap
