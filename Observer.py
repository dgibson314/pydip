from BaseClient import BaseClient

class Observer(BaseClient):
    def __init__(self, host='127.0.0.1', port=16713):
        BaseClient.__init__(self, host, port)
        self.name = 'ObserverBot'
        self.version = '1.0'

    def register(self):
        if not self.connected:
            self.connect()
        self.send_initial_msg()
        self.send_OBS()


if __name__ == '__main__':
    obs = Observer()
    obs.register()
    while True:
        msg = obs.recv_msg()
        if msg:
            #obs.handle_incoming_message(msg)
            obs.print_incoming_message(msg)
