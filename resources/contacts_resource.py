from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask_restful import Resource, request

from utils import contact_validators, neo4j_connector


class Contacts(Resource):
    @jwt_required
    def get(self, contact_id=None):
        if contact_id is None:
            current = neo4j_connector.get_first_level_contacts(get_jwt_identity())
            return {"message": "Success", "data": current}
        elif contact_validators.validate_email_format(contact_id):
            contact = neo4j_connector.find_user_by_email(contact_id)
            if contact is not None:
                return {"message": "Success", "data": contact}
            else:
                return {"message": "User with email: " + contact_id + " not found"}
        else:
            return {"message": "Invalid email"}

    @jwt_required
    def post(self, contact_id=None):
        if contact_id is None:
            return {"message": "Cannot add contact without an email"}, 400
        elif contact_validators.validate_email_format(contact_id) is False:
            return {"message": "Incorrect email address"}, 400
        elif contact_id == get_jwt_identity():
            return {"message": "Cannot add same user as a contact"}, 400
        else:
            contact = neo4j_connector.find_user_by_email(contact_id)
            if contact is not None:
                current_user = neo4j_connector.find_user_by_email(get_jwt_identity())
                status = neo4j_connector.add_contact(current_user, contact)
                if status:
                    return {"message": "Success"}
                else:
                    return {"message": "Already exists"}
            else:
                return {"message": "Non existing email address"}, 400

    @jwt_required
    def delete(self, contact_id=None):
        if contact_id is None:
            return {"message": "Cannot remove contact without an email"}, 400
        elif contact_validators.validate_email_format(contact_id) is False:
            return {"message": "Incorrect email address"}, 400
        elif contact_id == get_jwt_identity():
            return {"message": "Cannot add same user as a contact"}, 400
        elif neo4j_connector.check_contact_exists(get_jwt_identity(), contact_id) is False:
            return {"message": "Cannot remove non existing contact"}, 400
        else:
            neo4j_connector.remove_contact(get_jwt_identity(), contact_id)
            return {"message": "Success"}


class Recommendations(Resource):
    @jwt_required
    def get(self):
        args = request.args
        limit = args.get("limit")
        if limit is None:
            return {"message": "success", "data": neo4j_connector.get_recommended_contacts(get_jwt_identity())}
        else:
            return {"message": "success", "data": neo4j_connector.get_recommended_contacts(get_jwt_identity(), limit)}
