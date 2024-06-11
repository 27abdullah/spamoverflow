import datetime
from . import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
import rfc3339

class Email(db.Model):
    __tablename__ = 'spamoverflows'

    email_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer = db.Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    to_addr = db.Column(db.String(220), nullable=True)
    from_addr = db.Column(db.String(220), nullable=True)
    subject = db.Column(db.String(220), nullable=True)
    status = db.Column(db.String(8), nullable=True, default='pending')
    malicious = db.Column(db.Boolean, nullable=True)
    domains = db.Column(db.String(220), nullable=True)
    meta_data = db.Column(db.String(220), nullable=True)
    high_priority = db.Column(db.Boolean)

    def to_response(self):
        return {
            'id': self.email_id,
            'created_at': rfc3339.rfc3339(self.created_at),
            'updated_at': rfc3339.rfc3339(self.updated_at),
            'contents': {
                'to': self.to_addr,
                'from': self.from_addr,
                'subject': self.subject,
            },           
            'status': self.status,
            'malicious': self.malicious,
            'domains': eval(self.domains) if self.domains else [],
            'metadata': {
                "spamhammer": self.meta_data
            }
        }
        
    def __repr__(self):
        return f'<spamoverflow {self.uuid} {self.to_addr}>'