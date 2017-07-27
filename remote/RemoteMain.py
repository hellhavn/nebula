import sys

from common.Instance import Instance
from common_util import *
from remote.NebrInstance import NebrInstance
from remote.RemoteController import RemoteController
from remote.function.migrate_db import migrate_db

from remote.function.query_db import list_users, list_clouds, list_hosts
from remote.function.create import create
from remote.function.new_user import new_user


def start(instance, argv):
    remote_controller = RemoteController(instance)
    remote_controller.start(argv=argv)


def kill(instance, argv):
    rd = instance.kill()
    print(rd.data)


commands = {
    'new-user': new_user
    , 'start': start
    , 'create': create
    , 'list-users': list_users
    , 'list-clouds': list_clouds
    , 'migrate-db': migrate_db
    , 'kill': kill
    , 'list-hosts': list_hosts
}
command_descriptions = {
    'new-user': '\tadd a new user to the database'
    , 'start': '\t\tstart the remote server'
    , 'create': '\t\tcreate a new cloud to track'
    , 'list-users': '\tlist all current users'
    , 'list-clouds': '\tlist all current clouds'
    , 'migrate-db': '\tPerforms a database upgrade. This probably shouldn\'t be callable by the user'
    , 'kill': '\t\tkills an instance if it\'s running.'
    , 'list-hosts': '\t\tLists details about hosts'
}


def usage(instamce, argv):
    print 'usage: nebr <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebr_main(argv):
    if len(argv) < 2:
        usage(None, argv)
        sys.exit(0)

    working_dir, argv = Instance.get_working_dir(argv, True)
    log_path, argv = get_log_path(argv)
    log_level, argv = get_log_verbosity(argv)

    config_logger('nebr', log_path, log_level)
    _log = get_mylog()

    _log.info('Configured logging {}, {}'.format(log_path, log_level))
    if log_path is not None:
        print 'Writing log to {}'.format(log_path)

    nebr_instance = NebrInstance(working_dir)

    # if there weren't any args, print the usage and return
    # Do this again, because get_working_dir may have removed all the args
    if len(argv) < 2:
        usage(None, argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(nebr_instance, argv[2:])
    sys.exit(0)

if __name__ == '__main__':
    nebr_main(sys.argv)


