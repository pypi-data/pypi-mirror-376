from .auth_provider import AuthProvider
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import redirect
from django.urls import path
from rest_framework.permissions import AllowAny
from .samlsp import SAMLSP

class SAMLProvider(AuthProvider):
    def __init__(self, title: str, name: str, conf: dict):
        super().__init__(title, name, conf.get('populate_user', 'drf_sso.providers.user_population.base_user_population'))
        self._init_provider_api(conf["config"])
        
    def _init_provider_api(self, config: dict):
        config["sp"]["acs_url"] = f"{self.base_url}callback/"
        self.provider = SAMLSP(config["sp"], config["idp_meta_url"])
        
    def get_routes(self):
        @api_view(["GET"])
        @permission_classes([AllowAny])
        def login_view(request):
            (_, url, _) = self.provider.get_login_request()
            return redirect(url)
        
        return super().get_routes() + [
            path(f"{self.name}/login/", login_view, name=f"sso-{self.name}-login")
        ]
    
    def get_login_url(self):
        return f"{self.base_url}login/"
    
    def validate_response(self, request):
        response = request.data.get("SAMLResponse")
        if response is None:
            raise Exception("SAML Response not found.")
        response = self.provider.parse_response(response, relay_state=request.data.get("RelayState"))
        if not response.is_valid():
            raise Exception("SAML Response invalid.")
        
        attributes = response.get_attributes()
        attributes['subject'] = response.get_subject()
        
        return attributes