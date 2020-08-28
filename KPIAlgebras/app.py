from flask import Flask
from KPIAlgebras.rest import endpoints

def create_app():
    app = Flask(__name__)
    app.register_blueprint(endpoints.blueprint)
    return app