from datetime import datetime, timedelta

from remote import _remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref

__author__ = 'Mike'


class HostHostFetchMapping(db.Base):
    __tablename__ = 'hosthostfetchmapping'
    id = Column(Integer, primary_key=True)
    new_host_id = Column(ForeignKey('host.id'))
    old_host_id = Column(ForeignKey('host.id'))
    cloud_id = Column(ForeignKey('cloud.id'))

    created_on = Column(DateTime)

    def has_timed_out(self):
        delta = datetime.utcnow() - self.created_on
        return (delta.seconds/60) > 30

    def __init__(self, old_host, new_host, cloud):
        self.cloud_id = cloud.id
        self.old_host_id = old_host.id
        self.new_host_id = new_host.id
        self.created_on = datetime.utcnow()

