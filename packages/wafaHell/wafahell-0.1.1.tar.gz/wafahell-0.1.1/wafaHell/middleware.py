import re
from flask import request, abort
from urllib.parse import unquote

class WafaHell:
    def __init__(self, app=None, block_code=403, log_func=None, monitor_mode=False):
        self.app = app
        self.block_code = block_code
        self.log_func = log_func or (lambda msg: print(f"[WAF] {msg}"))
        self.monitor_mode = monitor_mode
        # Regras básicas
        self.rules = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDROP\b)",  
            r"' OR '1'='1",                                
            r"<script.*?>.*?</script>",                    
            r"javascript:",                                
        ]

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        @app.before_request
        def waf_check():
            if self.is_malicious(request):
                self.log_attack(request)
                if not self.monitor_mode:
                    abort(self.block_code)

    def detect_attack(self, data: str) -> bool:
        for pattern in self.rules:
            if re.search(pattern, data, re.IGNORECASE):
                return True
        return False

    def is_malicious(self, req) -> bool:
        # URL + Query Params
        if self.detect_attack(req.url) or any(self.detect_attack(v) for v in req.args.values()):
            return True

        # Headers
        for _, value in req.headers.items():
            if self.detect_attack(value):
                return True

        # Body
        if req.data and self.detect_attack(req.data.decode(errors="ignore")):
            return True

        return False

    def log_attack(self, req):
        ip = req.remote_addr
        user_agent = req.headers.get("User-Agent", "unknown")
        path = req.path
        query = req.query_string.decode(errors="ignore") if req.query_string else ""
        
        msg = (
            f"Ataque detectado\n",
            f"IP: {ip}\n"
            f"User-Agent: {user_agent}\n"
            f"Rota: {path}\n"
            f"Query: {unquote(query)}\n"
        )
        self.log_func(msg)
