from py2neo import Graph, Node, Relationship

from utils.config import DataBaseConfig

graph = Graph(host=DataBaseConfig.host, port=DataBaseConfig.port,
              auth=(DataBaseConfig.username, DataBaseConfig.password))


def find_user_by_email(email, retrieve_password=False):
    user = graph.nodes.match("User", email=email).first()
    if user is not None and not retrieve_password:
        user.pop("password", None)
    return user


def delete_user_by_email(email):
    query = "MATCH (m:User) WHERE m.email=\"{email}\" Delete m"
    query = query.format(email=email)
    graph.run(query)
    return


def find_users(search_string, current_user):
    if search_string is None:
        return None
    else:
        query = "MATCH (m:User) WHERE m.email <> \"{user_email}\" and  ANY(prop in keys(m) where (not(prop = " \
                "\"password\") and toString(m[prop]) =~ \"(?i){search_string}.*\")) RETURN m; "
        query = query.format(search_string=search_string, user_email=current_user)
        contact_list = graph.run(query).to_table()
        for idx, record in enumerate(contact_list):
            del record[0]["password"]
            contact_list[idx] = record[0]
        return contact_list


def add_user(data):
    if not find_user_by_email(data["email"]):
        user = Node("User")
        for key, value in data.items():
            user[key] = value
        graph.create(user)
        return True
    else:
        return False


def add_contact(user, contact):
    contact_rel = Relationship(user, "CONTACT", contact)
    if contact_rel is not None:
        graph.create(contact_rel)
    return True


def check_contact_exists(user_id, contact_id):
    user = find_user_by_email(user_id)
    if user is None:
        return None
    else:
        query = "MATCH (node:User) -[:CONTACT]- (contact:User) WHERE node.email=\"{email_user}\" and " \
                "contact.email=\"{email_contact}\" return contact "
        query = query.format(email_user=user_id, email_contact=contact_id)
        contact_list = graph.run(query).to_table()
        return len(contact_list) == 1


def get_first_level_contacts(user_id):
    user = find_user_by_email(user_id)
    if user is None:
        return None
    else:
        query = "MATCH (node:User) -[:CONTACT]- (contact:User) WHERE node.email=\"{email}\" RETURN contact"
        query = query.format(email=user_id)
        contact_list = graph.run(query).to_table()
        for idx, record in enumerate(contact_list):
            del record[0]["password"]
            contact_list[idx] = record[0]
        return contact_list


def get_recommended_contacts(user_id, limit=3):
    user = find_user_by_email(user_id)
    if user is None:
        return None
    else:
        query = "MATCH (n:User)-[:CONTACT]-(:User)-[:CONTACT]-(o:User) where" \
                " n.email=\"{email}\" and not((n)-[:CONTACT]-(o))" \
                " RETURN o,count(*) " \
                "order by count(*) desc LIMIT {limit} "
        query = query.format(email=user_id, limit=limit)
        contact_list = graph.run(query).to_table()
        for idx, record in enumerate(contact_list):
            del record[0]["password"]
            contact_list[idx] = record[0]
        return contact_list


def remove_contact(user_id, contact_id):
    query = "MATCH (node:User) -[r:CONTACT]- (contact:User) WHERE node.email=\"{email_user}\" and contact.email=\"{" \
            "email_contact}\" DELETE r "
    query = query.format(email_user=user_id, email_contact=contact_id)
    graph.run(query)
    return
