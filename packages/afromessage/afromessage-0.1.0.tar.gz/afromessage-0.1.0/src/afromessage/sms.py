from .utils import handle_error, log_request, log_response
import requests

class SMS:
    def __init__(self, client):
        self.client = client

    def send(self, to, message, callback=None, from_=None, sender=None, template=0):
        """Send a single SMS"""
        try:
            body = {
                'to': to,
                'message': message,
                'callback': callback,
                'from': from_,
                'sender': sender,
                'template': template
            }
            # Remove None values
            body = {k: v for k, v in body.items() if v is not None}
            
            log_request("send", "post", body)
            
            response = self.client.post("send", json=body)
            response_data = response.json()
            
            log_response("send", response_data)
            return response_data
        except Exception as err:
            raise handle_error(err)

    def bulk_send(self, to, message, from_=None, sender=None, campaign=None):
        """Send bulk SMS"""
        try:
            body = {
                'to': to,
                'message': message,
                'from': from_,
                'sender': sender,
                'campaign': campaign
            }
            # Remove None values
            body = {k: v for k, v in body.items() if v is not None}
            
            log_request("bulk_send", "post", body)
            
            response = self.client.post("bulk_send", json=body)
            response_data = response.json()
            
            log_response("bulk_send", response_data)
            return response_data
        except Exception as err:
            raise handle_error(err)