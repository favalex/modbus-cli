import logging

from .access import dump


class ModbusRtu:
    def __init__(self, device, baud, stop_bits, slave_id):
        self.device = device
        self.baud = baud
        self.stop_bits = stop_bits
        if not slave_id:
            slave_id = 1
        self.slave_id = slave_id

        import umodbus.client.serial.rtu as modbus
        self.protocol = modbus

    def connect(self):
        from serial import Serial, PARITY_NONE

        self.connection = Serial(port=self.device, baudrate=self.baud, parity=PARITY_NONE,
                                 stopbits=self.stop_bits, bytesize=8, timeout=5)

    def send(self, request):
        self.connection.write(request)

    def receive(self, request):
        response = self.connection.read(2)
        if len(response) != 2:
            raise RuntimeError('timeout')
        slave_id, function = response

        if function in (1, 2, 3, 4):
            # Functions with variable size
            response += self.connection.read(1)
            count = 2 + response[-1]
            response += self.connection.read(count)
        elif function in (5, 15):
            # Function with fixed size
            response += self.connection.read(6)
        elif function & 0x80:
            response += self.connection.read(3)
        else:
            raise NotImplementedError('RTU function {}'.format(function))

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
