###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

import sys

from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File

import txaio

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, listenWS
# from twisted.internet.endpoints import IPv6Address

class EchoServerProtocol(WebSocketServerProtocol):

    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)


if __name__ == '__main__':

    txaio.start_logging(level='debug')

    # SSL server context: load server key and certificate
    # We use this for both WS and Web!
    contextFactory = ssl.DefaultOpenSSLContextFactory('c:\\users\\zadjii\\dev\\public\\nebula\\instances\\host\\sunio\\host.key',
                                                      'c:\\users\\zadjii\\dev\\public\\nebula\\instances\\host\\sunio\\host.crt')

    ws_host = "[::1]"
    ws_initial_url = "wss://{}:0".format(ws_host)
    print('Initial URL = "{}"'.format(ws_initial_url))

    # factory = WebSocketServerFactory(u"wss://127.0.0.1:0")
    factory = WebSocketServerFactory(ws_initial_url)
    # by default, allowedOrigins is "*" and will work fine out of the
    # box, but we can do better and be more-explicit about what we
    # allow. We are serving the Web content on 8080, but our WebSocket
    # listener is on 9000 so the Origin sent by the browser will be
    # from port 8080...
    factory.setProtocolOptions(
        allowedOrigins=[
            "https://127.0.0.1:8080",
            "https://localhost:8080",
        ]
    )

    factory.protocol = EchoServerProtocol

    listener = listenWS(factory, contextFactory, interface='::')
    # print('"wss://127.0.0.1:{}"'.format(listener.getHost().port))

    ws_actual_url = "wss://{}:{}".format(ws_host ,listener.getHost().port)
    print('Actual URL = "{}"'.format(ws_actual_url))
    webdir = File(".")
    webdir.contentTypes['.crt'] = 'application/x-x509-ca-cert'
    web = Site(webdir)
    reactor.listenSSL(0, web, contextFactory)
    #reactor.listenTCP(8080, web)

    reactor.run()