from .utils import handle_error, log_request, log_response
import requests

class Challenge:
    def __init__(self, client):
        self.client = client

    def challenge(self, to, pr=None, ps=None, callback=None, sb=None, sa=None, 
                 ttl=None, len_=None, t=None, from_=None, sender=None):
        """Initiate an OTP challenge"""
        try:
            params = {
                'to': to,
                'pr': pr,
                'ps': ps,
                'callback': callback,
                'sb': sb,
                'sa': sa,
                'ttl': ttl,
                'len': len_,
                't': t,
                'from': from_,
                'sender': sender
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            log_request("challenge", "get", params)
            
            response = self.client.get("challenge", params=params)
            response_data = response.json()
            
            log_response("challenge", response_data)
            return response_data
        except Exception as err:
            raise handle_error(err)

    def verify(self, to, code):
        """Verify an OTP code"""
        try:
            params = {
                'to': to,
                'code': code
            }
            
            log_request("verify", "get", params)
            
            response = self.client.get("verify", params=params)
            response_data = response.json()
            
            log_response("verify", response_data)
            return response_data
        except Exception as err:
            raise handle_error(err)