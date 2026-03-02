from app import create_app
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173"]}},
     supports_credentials=True)