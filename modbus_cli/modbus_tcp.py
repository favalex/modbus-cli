import struct
import logging
import time

from .access import dump


class ModbusTcp:
    def __init__(self, host, port, slave_id, timeout):
        self.host = host
        self.port = port
        if not slave_id:
            slave_id = 255
        self.slave_id = slave_id
        self.timeout = timeout

        import umodbus.client.tcp as modbus

        self.protocol = modbus

    def connect(self):
        import socket

        addr_info = socket.getaddrinfo(
            self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )

        for af, socktype, proto, _, sa in addr_info:
            try:
                self.connection = socket.socket(af, socktype, proto)
                self.connection.connect(sa)
                self.connection.settimeout(self.timeout)
                return
            except OSError:
                if self.connection:
                    self.connection.close()
        raise OSError(f"Could not connect to {self.host}")

    def send(self, request):
        self.connection.send(request)

    def receive(self, request):
        header = self.receive_n(6)
        seq, _, count = struct.unpack(">3H", header)
        sent_seq = struct.unpack(">H", request[:2])[0]
        if seq != sent_seq:
            logging.warn("Sequence mismatch: sent %s, received %s", sent_seq, seq)
        response = header + self.receive_n(count)

        logging.debug("← < %s > %s bytes", dump(response), len(response))

        return self.protocol.parse_response_adu(response, request)

    def receive_n(self, n):
        data = bytes()
        while len(data) < n:
            len_before = len(data)
            data += self.connection.recv(n - len(data))
            if len(data) == len_before:
                time.sleep(0.1)
        return data

    def close(self):
        self.connection.close()

    def perform_accesses(self, accesses, definitions):
        for access in accesses:
            if access.write:
                access.write_registers_send(self)
            else:
                access.read_registers_send(self)

        for access in accesses:
            if access.write:
                access.write_registers_receive(self)
            else:
                access.read_registers_receive(self)
                access.print_values(definitions)

        return self
