from .base_client import BaseClient
from .types import RequestOptions, WxOfficialAccountTokenResponse, WxJsapiTicketResponse, WxSignatureRequest, WxSignatureResponse, WxMiniProgramTokenResponse

class TokenService(BaseClient):
    def __init__(self, config):
        super().__init__(config, 'token')
    
    def get_wx_official_account_token(self, appid: str, options: RequestOptions = None) -> WxOfficialAccountTokenResponse:
        return self.request('/wxh5/accesstoken', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))
    
    def get_wx_jsapi_ticket(self, appid: str, options: RequestOptions = None) -> WxJsapiTicketResponse:
        return self.request('/wxh5/jsapi_ticket', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))
    
    def get_wx_signature(self, signature_request: WxSignatureRequest, options: RequestOptions = None) -> WxSignatureResponse:
        return self.request('/wxh5/signature', RequestOptions(
            method='POST',
            body=signature_request,
            headers=options.headers if options else None
        ))
    
    def get_wx_mini_program_token(self, appid: str, options: RequestOptions = None) -> WxMiniProgramTokenResponse:
        return self.request('/wxmp/accesstoken', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))