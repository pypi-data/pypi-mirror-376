from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from importlib import import_module

USER = get_user_model()

DEFAULTS = {
    "UNAUTHORIZED_MODELS": [USER.__name__],
    "UNAUTHORIZED_KEYS": ["password", "is_staff", "is_superuser"],
    "AUTHORIZATION_METHOD": "drf_query_lang.permission.base_permission"
}

def import_function(path: str):
    module_path, function_name = path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, function_name)

class DRFQueryLangSettings:
    def __init__(self):
        user_settings = getattr(django_settings, 'DRF_QUERY_LANG', {})
        
        for setting, default in DEFAULTS.items():
            setattr(self, setting, user_settings.get(setting, default))

        if not isinstance(self.UNAUTHORIZED_MODELS, (list, tuple, set)):
            raise ImproperlyConfigured("DRF_QUERY_LANG['UNAUTHORIZED_MODELS'] must be a valid list, tuple or set.")
        
        if not isinstance(self.UNAUTHORIZED_KEYS, (list, tuple, set)):
            raise ImproperlyConfigured("DRF_QUERY_LANG['UNAUTHORIZED_KEYS'] must be a valid list, tuple or set.")
        
        if not isinstance(self.AUTHORIZATION_METHOD, str):
            raise ImproperlyConfigured("DRF_QUERY_LANG['AUTHORIZATION_METHOD'] must be a valid method ptr.")
        
        try:
            self.AUTHORIZATION_METHOD = import_function(self.AUTHORIZATION_METHOD)
            if not callable(self.AUTHORIZATION_METHOD):
                raise Exception("Authorization method is not callable.")
        except Exception as e:
            raise ImproperlyConfigured(f"DRF_QUERY_LANG['AUTHORIZATION_METHOD'] must be a valid method ptr. ({e})")
        
        self.UNAUTHORIZED_MODELS = list(self.UNAUTHORIZED_MODELS)
        self.UNAUTHORIZED_KEYS = list(self.UNAUTHORIZED_KEYS)
        
    def summary(self):
        return {
            "UNAUTHORIZED_MODELS": self.UNAUTHORIZED_MODELS,
            "UNAUTHORIZED_KEYS": self.UNAUTHORIZED_KEYS,
            "AUTHORIZATION_METHOD": self.AUTHORIZATION_METHOD.__name__,
        }

api_settings = DRFQueryLangSettings()