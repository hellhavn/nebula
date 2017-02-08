import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from remote.models import nebr_base as base


__author__ = 'Mike'


cloud_owners = Table(
    'cloud_owners'
    , base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )
cloud_contributors = Table(
    'cloud_contributors'
    , base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )


HIDDEN_CLOUD = 0  # only owners can access IP
PRIVATE_CLOUD = 1  # only owners and contributors
PUBLIC_CLOUD = 2  # anyone (host can still reject RDWR)
# todo: when making links, host needs to know privacy state. If a host wants to
# cont make a public link, then the cloud needs to be public, etc.


class Cloud(base):
    __tablename__ = 'cloud'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_on = Column(DateTime)
    owners = relationship(
        "User"
        , secondary=cloud_owners
        , backref=backref('owned_clouds', lazy='dynamic')
        , lazy='dynamic'
        )
    contributors = relationship(
        "User"
        , secondary=cloud_contributors
        , backref=backref('contributed_clouds', lazy='dynamic')
        , lazy='dynamic'
        )
    hosts = relationship('Host', backref='cloud', lazy='dynamic')
    last_update = Column(DateTime)
    max_size = Column(Integer)  # Cloud size in bytes
    privacy = Column(Integer, default=PRIVATE_CLOUD)

    creator_id = Column(ForeignKey('user.id'))
    # sessions = relationship('Session', backref='cloud', lazy='dynamic')

    def __init__(self, creator):
        self.creator_id = creator.id
        self.owners.append(creator)
        self.created_on = datetime.utcnow()
        self.last_update = datetime.utcnow()
        self.privacy = PRIVATE_CLOUD
        self.max_size = -1

    def is_hidden(self):
        return self.privacy == HIDDEN_CLOUD

    def is_private(self):
        return self.privacy == PRIVATE_CLOUD

    def is_public(self):
        return self.privacy == PUBLIC_CLOUD

    def has_owner(self, user):
        return self.owners.filter_by(id=user.id).first() is not None

    def has_contributor(self, user):
        return self.contributors.filter_by(id=user.id).first() is not None

    def add_owner(self, user):
        if not self.has_owner(user):
            self.owners.append(user)

    def add_contributor(self, user):
        if not self.has_contributor(user):
            self.contributors.append(user)

    def can_access(self, user):
        if self.is_hidden():
            return self.has_owner(user)
        elif self.is_private():
            return self.has_owner(user) or self.has_contributor(user)
        else:
            return True

    def active_hosts(self):
        hosts = []
        for host in self.hosts.all():
            if host.is_active():
                hosts.append(host)
        return hosts

    def creator_name(self):
        # todo/fixme: this is temporary until I add uname properly to the DB
        # first_owner = self.owners.first()
        # if first_owner is not None:
        #     return first_owner.username
        # return None
        return self.uname()

    def uname(self):
        return self.creator.username

    def cname(self):
        return self.name

    def full_name(self):
        return '{}/{}'.format(self.uname(), self.name)

    def to_dict(self):
        self_dict = {
            'uname': self.uname()
            , 'cname': self.cname()
            , 'created_on': self.created_on.isoformat() + 'Z"'
            , 'last_update': self.last_update.isoformat() + 'Z"'
            , 'max_size': self.max_size
            , 'privacy': self.privacy
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

