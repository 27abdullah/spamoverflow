from os import environ
from celery import Celery
import subprocess
import json

from spamoverflow.models.spamoverflow import Email
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.task_default_queue = os.environ.get("CELERY_DEFAULT_QUEUE", "spamworker")

engine = create_engine(environ.get("SQLALCHEMY_DATABASE_URI"))
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

@celery.task(name="spamworker")
def spamhammer(email_id, body, meta_data): 
    session = get_session()
    
    req = {
        "id": str(email_id),
        "content": body,
        "metadata": meta_data
    }

    email = session.query(Email).get(email_id)

    try:
        resp = subprocess.run(['./spamhammer', 'scan'], stdout=subprocess.PIPE,
                                input=json.dumps(req), text=True) 
        result = json.loads(resp.stdout)
        email.malicious = result.get('malicious')
        email.status = "scanned"
        session.commit()

    except Exception as e:
        email.status = 'failed'
        session.commit()
        
    finally:
        session.close()