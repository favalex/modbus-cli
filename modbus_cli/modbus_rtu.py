import logging

from .access import dump


class ModbusRtu:
    def __init__(self, device, baud, parity, stop_bits, slave_id):
        from serial import PARITY_EVEN, PARITY_ODD, PARITY_NONE
        parity_opts = { 'e': PARITY_EVEN, 'o': PARITY_ODD, 'n': PARITY_NONE }
        self.device = device
        self.baud = baud
        self.parity = parity_opts[parity]
        self.stop_bits = stop_bits
        if not slave_id:
            slave_id = 1
        self.slave_id = slave_id

        import umodbus.client.serial.rtu as modbus
        self.protocol = modbus

    def connect(self):
        from serial import Serial

        self.connection = Serial(port=self.device, baudrate=self.baud, parity=self.parity,
                                 stopbits=self.stop_bits, bytesize=8, timeout=5)

    def send(self, request):
        self.connection.write(request)

    def receive(self, request):
        response = self.connection.read(2)
        if len(response) != 2:
            raise RuntimeError('timeout')
        slave_id, function = response

        try:
            if function in (1, 2, 3, 4):
                # Functions with variable size
                response += self.connection.read(1)
                count = 2 + response[-1]
                response += self.connection.read(count)
            elif function in (5, 6, 15, 16):
                # Function with fixed size
                response += self.connection.read(6)
            elif function & 0x80:
                response += self.connection.read(3)
            else:
                response += self.connection.read(1024)
                raise NotImplementedError('RTU function {}'.format(function))
        finally:
            logging.debug('← < %s > %s bytes', dump(response), len(response))

        return self.protocol.parse_response_adu(response, request)

    def close(self):
        self.connection.close()

    def perform_accesses(self, accesses, definitions):
        for access in accesses:
            access.perform(self)
            if not access.write:
                access.print_values(definitions)

        return self
