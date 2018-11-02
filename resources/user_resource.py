from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
from flask_restful import Resource, reqparse, request
from passlib.hash import pbkdf2_sha256 as sha256

from utils import contact_validators, neo4j_connector, redis_connector

signupParser = reqparse.RequestParser(bundle_errors=True)
signupParser.add_argument('fname', type=str, help="Cannot be blank and should be text", required=True)
signupParser.add_argument('mname', type=str, help="Should be text")
signupParser.add_argument('lname', type=str, help="Should be text")
signupParser.add_argument('password', help="Cannot be blank", required=True)
signupParser.add_argument('email', help="Cannot be blank", required=True)
signupParser.add_argument('telephone', help="Cannot be blank", required=True)

loginParser = reqparse.RequestParser(bundle_errors=True)
loginParser.add_argument('password', help="Cannot be blank", required=True)
loginParser.add_argument('email', help="Cannot be blank", required=True)


def generate_hash(password):
    return sha256.hash(password)


def verify_hash(password, hash):
    return sha256.verify(password, hash)


class User(Resource):
    def post(self):
        data = signupParser.parse_args()
        user = neo4j_connector.find_user_by_email(data.email)
        if user is None:
            if contact_validators.validate_user_contact_details(data):
                data.password = generate_hash(data.password)
                if not neo4j_connector.add_user(data):
                    return {"message": "Error while creating new user"}, 500
                else:
                    access_token = create_access_token(identity=data["email"])
                    refresh_token = create_refresh_token(identity=data["email"])
                    return {
                        "message": "Signup complete",
                        "accessToken": access_token,
                        "refreshToken": refresh_token,
                        "user": {"fname": data["fname"]}
                    }
            else:
                send = {
                    "message": "User contact details are not valid.",
                    "data": {}
                }
                if not contact_validators.validate_telephone_number(data.telephone):
                    send["data"]["telephone"] = "invalid. requires e164 formatted number"
                if not contact_validators.validate_email_format(data.email):
                    send["data"]["email"] = "invalid"
                return send, 400
        else:
            return {"message": "User with same email already exists"}, 400

    @jwt_required
    def get(self):
        args = request.args
        if args.get("search") is None:
            return {"message": "success", "data": neo4j_connector.find_user_by_email(get_jwt_identity())}
        else:
            return {"message": "success", "data": neo4j_connector.find_users(args.get("search"), get_jwt_identity())}

    @jwt_required
    def delete(self):
        jti = get_raw_jwt()['jti']
        try:
            redis_connector.store_invalidated_token_details(jti)
        except:
            return {'message': 'Something went wrong'}, 500

        neo4j_connector.delete_user_by_email(get_jwt_identity())
        return {"message": "success", "data": {"removed": get_jwt_identity()}}


class UserLogin(Resource):
    def post(self):
        data = loginParser.parse_args()
        user = neo4j_connector.find_user_by_email(data.email, True)
        if user is None:
            return {"message": "No user found for email " + data.email}, 400
        else:
            if verify_hash(data.password, user["password"]):
                access_token = create_access_token(identity=data["email"])
                refresh_token = create_refresh_token(identity=data["email"])
                user.pop("password", None)
                return {
                    "message": 'Logged in as {}'.format(user["fname"]),
                    "accessToken": access_token,
                    "refreshToken": refresh_token,
                    "user": user
                }
            else:
                return {"message": "Wrong credentials"}, 401

    @jwt_required
    def delete(self):
        jti = get_raw_jwt()['jti']
        try:
            redis_connector.store_invalidated_token_details(jti)
            return {'message': 'Access accessToken has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500

    @jwt_refresh_token_required
    def put(self):
        current_user = get_jwt_identity()
        jti = get_raw_jwt()['jti']
        access_token = create_access_token(identity=current_user)
        redis_connector.store_invalidated_token_details(jti)
        refresh_token = create_refresh_token(identity=current_user)
        return {"message": "success", 'accessToken': access_token, 'refreshToken': refresh_token}
