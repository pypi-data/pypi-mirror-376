import requests
from .sms import SMS
from .challenge import Challenge

class AfroMessage:
    def __init__(self, token, base_url="https://api.afromessage.com/api/"):
        if not token:
            raise ValueError("AfroMessage token is required")
        
        self.token = token
        self.base_url = base_url
        
        # Create session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        self.session.timeout = 120  # 120 seconds timeout
        
        # Initialize API modules
        self.sms = SMS(self)
        self.challenge = Challenge(self)
    
    def request(self, method, endpoint, **kwargs):
        """Make HTTP requests"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def get(self, endpoint, **kwargs):
        """Convenience method for GET requests"""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        """Convenience method for POST requests"""
        return self.request('POST', endpoint, **kwargs)