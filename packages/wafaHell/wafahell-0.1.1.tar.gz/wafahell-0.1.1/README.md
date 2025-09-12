# WafHell

Middleware WAF for Flask, to detect SQLi and XSS.

## Instalation

```bash
pip install wafaHell
```

## Usage
```python
from flask import Flask
from flask_waf import FlaskWAF

app = Flask(__name__)
waf = FlaskWAF(app)
```