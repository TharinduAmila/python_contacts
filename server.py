from flask import jsonify, Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api

from resources import *
from utils import config, redis_connector

app = Flask(__name__, static_folder='public', static_url_path='')
app.url_map.strict_slashes = False
app.config['JWT_SECRET_KEY'] = config.FlaskAppConfig.jwt_secret
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['PROPAGATE_EXCEPTIONS'] = True
jwt = JWTManager(app)

api = Api(app)
api.add_resource(user_resource.User, '/user')
api.add_resource(user_resource.UserLogin, '/user/login')
api.add_resource(contacts_resource.Recommendations, '/contacts/recommendations')
api.add_resource(contacts_resource.Contacts, '/contacts', '/contacts/<string:contact_id>')


@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"message": "Resource or Method not available"}), 404


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return redis_connector.get_invalidated_token(jti) is not None
