from .exceptions import BadKeyError, MissingPromptError, MissingUuidError

class AnovaChat():
    BASE_URL = "https://api.backyardbandwidth.com"
    
    def __init__(self, api_key: str):
        import httpx
        
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-Api-Key": api_key},
            verify=False
        )
        
    def limits(self):
        resp = self.client.post("/api/v1/llm/limits")
        
        data = resp.json()
        
        if not data.get("success", False):
            raise BadKeyError("Invalid api key")
        
        return data
    
    def tokenize(self, prompt):
        resp = self.client.post("/api/v1/llm/tokenize", json={
            "prompt": prompt
        })
        
        data = resp.json()
        
        if not data.get("success", False):
            raise MissingPromptError("No prompt provided")
        
        return data
    
    def send(self, prompt):
        resp = self.client.post("/api/v1/llm/send", json={
            "prompt": prompt
        })
        
        data = resp.json()
        
        if not data.get("success", False):
            raise MissingPromptError("No prompt provided")
        
        return data
    
    def status(self, uuid):
        resp = self.client.post("/api/v1/llm/status", json={
            "uuid": uuid
        })
        
        data = resp.json()
        
        if not data.get("success", False):
            raise MissingUuidError("No valid UUID provided")
        return data
        