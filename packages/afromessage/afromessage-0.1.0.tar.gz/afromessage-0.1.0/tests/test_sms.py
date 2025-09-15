import pytest
import requests_mock
from afromessage import AfroMessage 

def test_send_sms():
    """Test sending an SMS"""
    client = AfroMessage(token="test_token")
    
    with requests_mock.Mocker() as m:
        # Mock the API response
        mock_response = {
            "acknowledge": "success",
            "response": {
                "code": "202",
                "message": "SMS is queued for delivery"
            }
        }
        
        m.post("https://api.afromessage.com/api/send", json=mock_response)
        
        # Test the method
        response = client.sms.send(
            to="+251911500681",
            message="Test message",
            from_="test_sender_id",
            sender="TestSender"
        )
        
        # Verify the request was made correctly
        assert m.called
        assert m.last_request.method == "POST"
        assert "to" in m.last_request.json()
        assert m.last_request.json()["to"] == "+251911500681"
        
        # Verify the response
        assert response["acknowledge"] == "success"