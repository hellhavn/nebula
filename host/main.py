import sys

from common_util import enable_vt_support
from host.Host import Host
from host.function.dbg_nodes import dbg_nodes
from host.function.list_clouds import list_clouds
from host.function.mirror import mirror
from host.function.tree import tree, db_tree


def start(argv):
    host_controller = Host()
    host_controller.start(argv=argv)


commands = {
    'mirror': mirror
    , 'start': start
    , 'list-clouds': list_clouds
    , 'tree': tree
    , 'db-tree': db_tree
    , 'dbg-nodes': dbg_nodes
}

command_descriptions = {
    'mirror': '\t\tmirror a remote cloud to this device'
    , 'start': '\t\tstart the main thread checking for updates'
    , 'list-clouds': '\tlist all current clouds'
    , 'tree': '\t\tdisplays the file structure of a cloud on this host.'
    , 'db-tree': '\tdisplays the db structure of a cloud on this host.'
    , 'export-nebs': '\tWrites out the .nebs of matching clouds as json'
}


def usage(argv):
    print 'usage: nebs <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebs_main(argv):
    # if there weren't any args, print the usage and return
    if len(argv) < 2:
        usage(argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    enable_vt_support()
    result = selected(argv[2:])
    result = 0 if result is None else result
    sys.exit(result)


if __name__ == '__main__':
    nebs_main(sys.argv)