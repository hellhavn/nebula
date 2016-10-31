import socket
import sys
from datetime import datetime
from threading import Thread

from OpenSSL import SSL

from common_util import send_error_and_close, Success, Error, enable_vt_support
from connections.RawConnection import RawConnection
from host.util import set_mylog_name, mylog
from messages import *
from msg_codes import *
from remote import User, Cloud, Host, get_db
from remote.function.client import respond_to_client_get_cloud_hosts
from remote.function.client_session_setup import setup_client_session,\
    get_cloud_host, host_verify_client
from remote.function.create import create
from remote.function.get_hosts import get_hosts_response
from remote.function.mirror import mirror_complete, host_request_cloud, \
    client_mirror, host_verify_host
from remote.function.new_user import new_user
from remote.util import get_user_from_session, validate_session_id, \
    get_cloud_by_name

__author__ = 'Mike'

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

KEY_FILE = 'remote/key'
CERT_FILE = 'remote/cert'
# todo this is jank AF
###############################################################################


def filter_func(connection, address):
    msg_obj = connection.recv_obj()
    msg_type = msg_obj.type
    # print 'The message is', msg_obj
    if msg_type == NEW_HOST:
        new_host_handler(connection, address, msg_obj)
    elif msg_type == HOST_HANDSHAKE:
        host_handshake(connection, address, msg_obj)
    elif msg_type == REQUEST_CLOUD:
        host_request_cloud(connection, address, msg_obj)
    elif msg_type == MIRRORING_COMPLETE:
        mirror_complete(connection, address, msg_obj)
    elif msg_type == GET_HOSTS_REQUEST:
        get_hosts_response(connection, address, msg_obj)
    elif msg_type == GET_ACTIVE_HOSTS_REQUEST:
        get_hosts_response(connection, address, msg_obj)
    elif msg_type == CLIENT_SESSION_REQUEST:
        setup_client_session(connection, address, msg_obj)
    elif msg_type == CLIENT_GET_CLOUDS_REQUEST:
        respond_to_get_clouds(connection, address, msg_obj)
    elif msg_type == CLIENT_GET_CLOUD_HOST_REQUEST:
        get_cloud_host(connection, address, msg_obj)
    elif msg_type == CLIENT_GET_CLOUD_HOSTS_REQUEST:
        respond_to_client_get_cloud_hosts(connection, address, msg_obj)
    elif msg_type == CLIENT_MIRROR:
        client_mirror(connection, address, msg_obj)
    elif msg_type == HOST_VERIFY_CLIENT_REQUEST:
        host_verify_client(connection, address, msg_obj)
    elif msg_type == HOST_VERIFY_HOST_REQUEST:
        host_verify_host(connection, address, msg_obj)
    elif msg_type == CLIENT_ADD_OWNER:
        client_add_owner(connection, address, msg_obj)
    elif msg_type == ADD_CONTRIBUTOR:
        host_add_contributor(connection, address, msg_obj)
    elif msg_type == CLIENT_SESSION_REFRESH:
        client_session_refresh(connection, address, msg_obj)
    else:
        print 'I don\'t know what to do with', msg_obj
    connection.close()


def host_handshake(connection, address, msg_obj):
    db = get_db()
    ipv6 = msg_obj.ipv6
    host = db.session.query(Host).get(msg_obj.id)
    if host is not None:
        if not host.ipv6 == ipv6:
            mylog('Host [{}] moved from "{}" to "{}"'.format(host.id, host.ipv6, ipv6))
        host.ipv6 = ipv6
        host.port = msg_obj.port
        host.ws_port = msg_obj.wsport
        host.last_handshake = datetime.utcnow()
        db.session.commit()


def client_session_refresh(connection, address, msg_obj):
    db = get_db()
    session_id = msg_obj.sid
    # refreshes the session
    rd = validate_session_id(db, session_id)
    # db.session.commit()

    if not rd.success:
        mylog('Remote failed to refresh session {}, "{}"'.format(session_id, rd.data))
    # This particular message doesn't want a response


def respond_to_get_clouds(connection, address, msg_obj):
    db = get_db()
    session_id = msg_obj.sid
    rd = get_user_from_session(db, session_id)
    if not rd.success:
        mylog('generic CGCHsR error: "{}"'.format(rd.data), '31') # fixme
        send_generic_error_and_close(connection)
        return
    else:
        user = rd.data

    mylog('getting clouds for {}'.format(user.username))
    # owned_names = [c.name for c in user.owned_clouds.all()]
    # contributed_names = [c.name for c in user.contributed_clouds.all()]
    owned_clouds = [c.to_dict() for c in user.owned_clouds.all()]
    contributed_clouds = [c.to_dict() for c in user.contributed_clouds.all()]
    msg = ClientGetCloudsResponseMessage(
        session_id
        , owned_clouds
        , contributed_clouds
    )
    connection.send_obj(msg)


def new_host_handler(connection, address, msg_obj):
    db = get_db()
    print 'Handling new host'
    host = Host()
    host.ipv4 = address[0]
    host.ipv6 = msg_obj.ipv6
    host.port = msg_obj.port
    db.session.add(host)
    db.session.commit()

    msg = AssignHostIdMessage(host.id, 'todo_placeholder_key', 'todo_placeholder_cert')
    connection.send_obj(msg)


def client_add_owner(connection, address, msg_obj):
    # type: (AbstractConnection, object, ClientAddOwnerMessage) -> None
    if not msg_obj.type == CLIENT_ADD_OWNER:
        msg = 'Somehow tried to client_add_owner without CLIENT_ADD_OWNER'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return

    db = get_db()
    session_id = msg_obj.sid
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    new_user_id = msg_obj.new_user_id

    rd = validate_session_id(db, session_id)
    if not rd.success:
        err = AddOwnerFailureMessage(rd.data)
        send_error_and_close(err, connection)
        return
    else:
        sess_obj = rd.data
        user = sess_obj.user

    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    if not cloud.has_owner(user):
        msg = 'User "{}" is not an owner of the cloud "{}"'.format(user.username, (cloud_uname, cloudname))
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    new_owner = db.session.query(User).get(new_user_id)
    if new_owner is None:
        msg = 'No matching user {}'.format(new_user_id)
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    cloud.add_owner(new_owner)
    db.session.commit()
    response = AddOwnerSuccessMessage(session_id, new_user_id, cloud_uname, cloudname)
    connection.send_obj(response)
    connection.close()


def host_add_contributor(connection, address, msg_obj):
    # type: (AbstractConnection, object, AddContributorMessage) -> None
    if not msg_obj.type == ADD_CONTRIBUTOR:
        msg = 'Somehow tried to host_add_contributor without ADD_CONTRIBUTOR'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return
    mylog('host_add_contributor')
    db = get_db()
    host_id = msg_obj.host_id
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    new_user_id = msg_obj.new_user_id

    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    source_host = cloud.hosts.filter_by(id=host_id).first()
    if source_host is None:
        msg = 'No matching host {}'.format(host_id)
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    new_owner = db.session.query(User).get(new_user_id)
    if new_owner is None:
        msg = 'No matching user {}'.format(new_user_id)
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    cloud.add_contributor(new_owner)
    db.session.commit()
    response = AddContributorSuccessMessage(new_user_id, cloud_uname, cloudname)
    mylog('host_add_contributor success')
    connection.send_obj(response)
    connection.close()


def start(argv):
    set_mylog_name('nebr')
    enable_vt_support()
    context = SSL.Context(SSL.SSLv23_METHOD)
    context.use_privatekey_file(KEY_FILE)
    context.use_certificate_file(CERT_FILE)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s = SSL.Connection(context, s)
    address = (HOST, PORT) # ipv4
    # address = (HOST, PORT, 0, 0) # ipv6
    s.bind(address)
    mylog('Listening on {}'.format(address))

    s.listen(5)
    while True:
        (connection, address) = s.accept()
        raw_connection = RawConnection(connection)
        mylog('Connected by {}'.format(address))
        # This is kinda really dumb.
        # I guess the thread just catches any exceptions and prevents the main
        #   from crashing> otherwise it has no purpose
        # spawn a new thread to handle this connection
        thread = Thread(target=filter_func, args=[raw_connection, address])
        thread.start()
        thread.join()
        # echo_func(connection, address)
        # todo: possible that we might want to thread.join here.
        # cont  Make it so that each req gets handled before blindly continuing


def list_users(argv):
    db = get_db()
    # users = User.query.all()
    users = db.session.query(User).all()
    print 'There are ', len(users), 'users.'
    print '[{}] {:16} {:16}'.format('id', 'name', 'email')
    for user in users:
        print '[{}] {:16} {:16}'.format(user.id, user.name, user.email)


def list_clouds(argv):
    db = get_db()
    # clouds = Cloud.query.all()
    clouds = db.session.query(Cloud).all()
    print 'There are ', len(clouds), 'clouds.'
    print '[{}] {:16} {:16} {:16}'.format('id', 'name', 'max_size', 'owners')
    for cloud in clouds:
        owners = ''
        for owner in cloud.owners:
            owners = owners + owner.name + ' '
        print '[{}] {:16} {:16} {}'\
            .format(cloud.id, cloud.name, cloud.max_size, owners)


commands = {
    'new-user': new_user
    , 'start': start
    , 'create': create
    , 'list-users': list_users
    , 'list-clouds': list_clouds
}
command_descriptions = {
    'new-user': '\tadd a new user to the database'
    , 'start': '\t\tstart the remote server'
    , 'create': '\t\tcreate a new cloud to track'
    , 'list-users': '\tlist all current users'
    , 'list-clouds': '\tlist all current clouds'
}


def usage(argv):
    print 'usage: nebr <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebr_main(argv):
    if len(argv) < 2:
        usage(argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(argv[2:])
    sys.exit(0)


if __name__ == '__main__':
    nebr_main(sys.argv)
