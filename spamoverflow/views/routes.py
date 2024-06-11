from flask import Blueprint, jsonify, request
from spamoverflow.models import db
from spamoverflow.models.spamoverflow import Email
from datetime import datetime
from find_domains import find_domains
from uuid import UUID
import iso8601
import rfc3339
from spamoverflow.tasks import spamworker
from sqlalchemy.sql import func

api = Blueprint('api', __name__, url_prefix='/api/v1')
 
"""
Query the health of the service.
"""
@api.route('/health') 
def health():
    return jsonify({"status": "ok"})

"""
List all submitted emails for a given customer.
"""
@api.route('/customers/<customer_id>/emails', methods=['GET'])
def get_emails(customer_id):
    if not is_valid_uuid(customer_id):
        return bad_request("uuid")

    emails = db.session.query(Email).filter_by(customer=customer_id)

    if (start := request.args.get('start')):
        try:
            start = iso8601.parse_date(start.replace(" ", "+"))
        except iso8601.iso8601.ParseError as e:
            return bad_request(str(e) + ", start" + " " + request.args.get('start'))
        emails = emails.filter(Email.created_at >= start)

    if (end := request.args.get('end')):
        try:
            end = iso8601.parse_date(end.replace(" ", "+"))
        except iso8601.iso8601.ParseError as e:
            return bad_request(str(e) + ", end" + " " + request.args.get('end'))
        emails = emails.filter(Email.created_at < end)

    if (mal := request.args.get('only_malicious')):            
        if mal == 'true':
            emails = emails.filter_by(malicious='true')
        elif mal != 'false':
            return bad_request("only_malicious")

    if (state := request.args.get('state')):
        if state not in ['pending', 'failed', 'scanned']:
            return bad_request()
        emails = emails.filter_by(state=state)

    if (to_addr := request.args.get('to')):
        if '@' not in to_addr:
            return bad_request()
        emails = emails.filter_by(to_addr=to_addr)

    if (from_addr := request.args.get('from')):
        if '@' not in from_addr:
            return bad_request()
        emails = emails.filter_by(from_addr=from_addr)
    
    limit = request.args.get('limit', default=100, type=int)
    
    if not(0 < limit and limit <= 1000):
        return bad_request("limit")
    
    offset = request.args.get('offset', default=0, type=int)

    if not(0 <= offset):
        return bad_request("offset")
    
    emails = emails.order_by(Email.created_at.asc()).offset(offset).limit(limit).all()
    return jsonify([email.to_response() for email in emails]), 200

"""
Defines bad request resposne
"""
def bad_request(msg="Client input"):
    return jsonify({"Error:": "Bad request - " + msg}), 400

"""
Get information for a particular email.
"""
@api.route('/customers/<customer_id>/emails/<email_id>', methods=['GET'])
def get_email(customer_id, email_id):
    if len(request.args) > 0:
        return jsonify({'error': 'Invalid path', 'args': request.args}), 400

    email = Email.query.get(email_id)

    if not email:
        return jsonify({'Error': "Email id not in db"}), 404

    if str(email.customer) != customer_id:
        return jsonify({'Error': 'Customer does not have that email'}), 404
    
    return jsonify(email.to_response()), 200

"""
Post a new email scan request.
"""
@api.route('/customers/<customer_id>/emails', methods=['POST'])
def post_email(customer_id):
    json = request.get_json(force=True)
    contents = json.get('contents')    

    #Parsing request##
    high_priority = customer_id[0:4] == '1111'
    meta_data = json.get('metadata').get('spamhammer')
    body = contents.get('body')

    email = Email(
        customer = customer_id,
        to_addr = contents.get('to'),
        from_addr = contents.get('from'),
        subject = contents.get('subject'),
        high_priority = high_priority,
        meta_data = meta_data,
        domains = str(list(find_domains(body)))
    )

    db.session.add(email)
    db.session.commit()

    spamworker.spamhammer.delay(email.email_id, body, meta_data)

    return jsonify(email.to_response()), 201
    
"""
Returns true iff valid uuid
"""
def is_valid_uuid(uuid):
    try:
        uuid_obj = UUID(uuid)
    except ValueError:
        return False
    return (str(uuid_obj) == uuid)

"""
Get malicious senders of emails.
"""
@api.route('/customers/<customer_id>/reports/actors', methods=['GET'])
def get_actors(customer_id):
    emails = db.session.query(Email.from_addr,func.count(Email.email_id)).filter_by(
        malicious=True,customer=customer_id).group_by(Email.from_addr).all()

    data = []
    for email in emails:
        data.append({"id": email[0], "count": email[1]})

    result = {
        "generated_at": rfc3339.rfc3339(datetime.now()),
        "total": len(emails),
        "data": data
    }

    return jsonify(result), 200

"""
Get the domains that appeared in malicious emails.
"""
@api.route('/customers/<customer_id>/reports/domains', methods=['GET'])
def get_domains(customer_id):
    domainss = db.session.query(Email.domains).filter_by(
        malicious=True, customer=customer_id).all()

    #TODO - make faster
    domains_map = {}
    for domains in domainss:
        domains = eval(str(domains[0])) #0 as SQLAlchemy returns tuples for cols
        for domain in domains:
            if domain in domains_map:
                domains_map[domain] += 1
            else:
                domains_map[domain] = 1
    
    data = []
    for domain, count in domains_map.items():
        data.append({"id": domain, "count": count})

    result = {
        "generated_at": rfc3339.rfc3339(datetime.now()),
        "total": len(domains_map),
        "data": data
    }

    return jsonify(result), 200

"""
Get users who have received malicious emails.
"""
@api.route('/customers/<customer_id>/reports/recipients', methods=['GET'])
def get_recipients(customer_id):
    emails = db.session.query(Email.to_addr, func.count(Email.email_id)).filter_by(
        malicious=True, customer=customer_id).group_by(Email.to_addr).all()

    data = []
    for email in emails:
        data.append({"id": email[0], "count": email[1]})

    result = {
        "generated_at": rfc3339.rfc3339(datetime.now()),
        "total": len(emails),
        "data": data
    }

    return jsonify(result), 200