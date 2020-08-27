from flask import Flask
from KPIAlgebras.rest import measurement

def create_app():
    app = Flask(__name__)
    app.register_blueprint(measurement.blueprint)
    return app