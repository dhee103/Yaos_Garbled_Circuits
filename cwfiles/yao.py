
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import math
import random
from cryptography.fernet import Fernet
import util

class Wire:
    # class to represent wire
    def __init__(self, source, sinks):
        self.source = source
        self.sinks = sinks
        self.value = -1
        self.key_0 = Fernet.generate_key()
        self.key_1 = Fernet.generate_key()
        self.p_bit = random.randint(0,1)

    def __str__(self):
        return "source: " + str(self.source) + " sinks: " + str(self.sinks) + " value: " + str(self.value)

    def __repr__(self):
        return "source: " + str(self.source) + " sinks: " + str(self.sinks) + " value: " + str(self.value)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Wire):
            return self.source == other.source and self.sink == other.sink
        return False

class Gate:
    # class to represent gate
    def __init__(self, inputs, output, type):
        self.inputs = inputs
        self.output = output
        self.type = type
        self.truth_table = Gate.get_truth_table(type)


    def __str__(self):
        return "inputs: " + str(self.inputs) + " output: " + str(self.output) + " type: " + str(self.type)

    def __repr__(self):
        return "inputs: " + str(self.inputs) + " output: " + str(self.output) + " type: " + str(self.type)

    def get_truth_table(type):
        truth_table = {'AND': {(0,0):0, (0,1):0, (1,0):0, (1,1):1, (0,):0, (1,):1},
                        'OR': {(0,0):0, (0,1):1, (1,0):1, (1,1):1, (0,):0, (1,):1},
                        'NOT': {(0,):1, (1,):0, 0:1, 1:0},
                        'NAND': {(0,0):1, (0,1):1, (1,0):1, (1,1):0, (0,):1, (1,):0},
                        'NOR': {(0,0):1, (0,1):0, (1,0):0, (1,1):0, (0,):1, (1,):0},
                        'XOR': {(0,0):0, (0,1):1, (1,0):1, (1,1):0, (0,):0, (1,):0},
                        'XNOR': {(0,0):1, (0,1):0, (1,0):0, (1,1):1, (0,):1, (1,):1}
                      }
        return truth_table[type]


# generate a circuit
class Circuit:
    # class to represent Circuit
    def __init__(self,json_circuit):
        self.gates, self.wires = Circuit.generate_circuit(json_circuit)
        # number of inputs
        self.inputs = len(json_circuit['alice'] + json_circuit.get('bob',[]))
        # Alice's inputs
        self.alice = json_circuit['alice']
        # Bob's inputs
        self.bob = json_circuit.get('bob',[])
        #circuit outputs
        self.output = json_circuit['out']
        self.name = json_circuit['name']
        #garbled table
        self.garbled_truth_table = Circuit.generate_garbled_truth_table(self.gates, self.wires, self.output)

    # generates circuit from json description
    def generate_circuit(json_circuit):
        gates = []
        wires = []

        for gate in json_circuit['gates']:
            gates.append(Gate(gate['in'], gate['id'], gate['type']))
            for input in gate['in']:
                # find wire with source & add gate['id'] to sinks
                wire = util.find_wire(input, wires)
                if wire is not None:
                    wire.sinks.append(gate['id'])
                else:
                    wires.append(Wire(input, [gate['id']]))

        for wire in json_circuit['out']:
            wires.append(Wire(wire, None))

        return gates, wires

    #generates whole circuit truth table, similar to evaluation
    def generate_garbled_truth_table(gates, wires, outputs ):

        garbled_table = {}
        for gate in gates:
            gate_id = gate.output
            num_inputs = len(gate.inputs)

            perms = util.generate_perms(num_inputs)
            for perm in perms:
                # gets the key value pairs for the gate inputs
                wire_0 = util.find_wire(gate.inputs[0], wires)
                ext_value_0 = wire_0.p_bit ^ int(perm[0])
                encryption_key_0 = wire_0.key_1 if bool(ext_value_0) else wire_0.key_0

                if num_inputs == 2:
                    wire_1 = util.find_wire(gate.inputs[1], wires)
                    ext_value_1 = wire_1.p_bit ^ int(perm[1])
                    encryption_key_1 = wire_1.key_1 if bool(ext_value_1) else wire_1.key_0
                    # evaluates inputs as per gate type
                    result = gate.truth_table[(ext_value_0, ext_value_1)]
                else:
                    result = gate.truth_table[(ext_value_0)]

                # locates the output wire and its key
                output = util.find_wire(gate.output, wires)
                output_key = output.key_1 if bool(result) else output.key_0

                # calculates external value for output wire
                output_val = result ^ output.p_bit
                # encrypts output key pair with one key
                f = Fernet(encryption_key_0)
                encryption = f.encrypt(output_key + bytes(output_val))

                if num_inputs == 2:
                    # encrypts the output key with the second key if two input gate
                    f = Fernet(encryption_key_1)
                    encryption = f.encrypt(encryption)

                # sets value in nested dictionary garbled_table
                encryptions = garbled_table.get(gate_id, {})
                encryptions[perm] = encryption
                garbled_table[gate_id] = encryptions

        return garbled_table

    def garble(circuit):
        circuit.gates[0].inputs = ()
        for gate in circuit.gates:
            gate.output = gate.truth_table[gate.inputs]
