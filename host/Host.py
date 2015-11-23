import sys
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol
from host import HOST_WS_HOST, HOST_WS_PORT
from host.function.dbg_nodes import dbg_nodes
from host.util import set_mylog_name, mylog

__author__ = 'Mike'
from threading import Thread

from host.function.mirror import mirror
from host.function.tree import db_tree, tree
from host.function.list_clouds import list_clouds
from host.function.local_updates import local_update_thread
from host.function.network_updates import receive_updates_thread
from msg_codes import *
try:
    import asyncio
except ImportError:  # Trollius >= 0.3 was renamed
    import trollius as asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory


def ws_thread_function(argv=[]):
    mylog('top of ws thread')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    factory = WebSocketServerFactory(u"ws://{}:{}".format(HOST_WS_HOST, HOST_WS_PORT), debug=False)
    factory.protocol = MyBigFuckingLieServerProtocol

    # loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', HOST_WS_PORT)
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()


def start(argv):
    set_mylog_name('nebs')
    # todo process start() args here
    # local_thread = Thread(target=local_update_thread, args=argv)
    network_thread = Thread(target=receive_updates_thread, args=argv)
    # local_thread.start()
    network_thread.start()
    ###############

    ws_thread = Thread(target=ws_thread_function, args=argv)
    ws_thread.start()

    ###############
    local_update_thread()
    # local_thread.join()
    # network_thread.join()
    print 'Both the local update checking thread and the network thread have exited.'


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
    selected(argv[2:])
    sys.exit(0)


if __name__ == '__main__':
    nebs_main(sys.argv)
