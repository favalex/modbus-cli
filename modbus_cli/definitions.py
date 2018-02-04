import re
import logging

REGISTER_RE = re.compile('([cdhi]@)?(\d+)(/[^:|]*)?([:|].*)?')


class Definitions:
    def __init__(self):
        self.registers = {}
        self.presenters = {}

    def parse(self, filenames):
        for filename in filenames:
            if filename:
                with open(filename) as f:
                    self.filename = filename
                    self.line = 0
                    accumulated_line = ''
                    for line in f:
                        self.line += 1
                        if line[0].isspace():
                            accumulated_line += line
                        else:
                            self.parse_line(accumulated_line)
                            accumulated_line = line
                    self.parse_line(accumulated_line)
        logging.info('Parsed %d registers definitions from %d files', len(self.registers), len(filenames))

    def parse_line(self, line):
        if not line:
            return

        line = line.split('#')[0]
        line = line.strip()
        if not line:
            return

        if line[0] in ':|':
            name, values = self.parse_presenter(line)
            self.presenters[name] = values
        else:
            parts = line.split()
            if len(parts) == 2:
                name, definition = parts

                if REGISTER_RE.match(definition):
                    self.registers[name] = definition
                else:
                    logging.warning('%s:%d:Invalid definition %r for register %r. Skipping it.',
                                    self.filename, self.line, definition, name)
            else:
                logging.warning('%s:%d:Invalid definition %r. Skipping it.',
                                self.filename, self.line, line)

    def parse_presenter(self, line):
        parts = line.split()

        name = parts[0]

        values = {}
        for definition in parts[1:]:
            value, symbol = definition.split('=')

            values[int(value, 0)] = symbol

        return name, values
