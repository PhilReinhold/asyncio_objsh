import asyncio

loop = asyncio.get_event_loop()
shared_objects = {}

class ObjectSharerError(Exception):
    pass

class RemoteException(Exception):
    pass

class MessageProtocol(asyncio.Protocol):
    transport = None
    data = b''
    length_target = 8
    header_received = False

    RETURN = 'r'
    ERROR = 'e'
    GET = 'g'
    INFO = 'i'

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.data += data

        while len(self.data) < self.length_target:
            segment = self.data[:self.length_target]
            self.data = self.data[self.length_target:]
            if self.header_received:
                self.message_received(segment[0], segment[1:])
                self.header_received = False
            else:
                self.length_target = int.from_bytes(segment, 'big')
                self.header_received = True

    def message_received(self, msg_type, msg_data):
        dispatch = {
            MessageProtocol.ERROR: self.error_received,
            MessageProtocol.RETURN: self.return_received,
            MessageProtocol.GET: self.get_received,
            MessageProtocol.INFO: self.info_received
        }
        return dispatch[msg_type](msg_data)

    def error_received(self, error):
        raise RemoteException(error)

    def return_received(self, ret):
        raise ObjectSharerError('return handler not implemented')

    def get_received(self, name):
        raise ObjectSharerError('get handler not implemented')

    def info_received(self, info):
        raise ObjectSharerError('info handler not implemented')

    def send_message(self, msg_type, msg_data):
        assert len(msg_type) is 1
        self.transport.write(msg_type + msg_data)

    def send_error(self, error):
        self.send_message(MessageProtocol.ERROR, error)

    def send_return(self, retval):
        self.send_message(MessageProtocol.RETURN, retval)

    def send_get(self, name):
        self.send_message(MessageProtocol.GET, name)

    def send_info(self, name):
        self.send_message(MessageProtocol.INFO, name)


class ObjectSharerProtocol(MessageProtocol):
    transport = None
    message = b''

    def get_received(self, name):
        if name not in shared_objects:
            self.send_error('no such object %s' % name)
        else:
            self.send_info(self.get_info(shared_objects[name]))

loop.create_connection
