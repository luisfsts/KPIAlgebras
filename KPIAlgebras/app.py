from flask import Flask
from KPIAlgebras.rest import endpoints
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.register_blueprint(endpoints.blueprint) 
    CORS(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5002)    
