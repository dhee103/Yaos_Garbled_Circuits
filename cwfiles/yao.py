
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import math
import random
from cryptography.fernet import Fernet
import util

class Wire:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink
        self.value = -1
        self.key_0 = Fernet.generate_key()
        self.key_1 = Fernet.generate_key()
        self.p_bit = random.randint(0,1)

    def __str__(self):
        return "source: " + str(self.source) + " sink: " + str(self.sink) + " value: " + str(self.value)

    def __repr__(self):
        return "source: " + str(self.source) + " sink: " + str(self.sink) + " value: " + str(self.value)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Wire):
            return self.source == other.source and self.sink == other.sink
        return False

class Gate:
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
                        'NOT': {(0,):1, (1,):0},
                        'NAND': {(0,0):1, (0,1):1, (1,0):1, (1,1):0, (0,):1, (1,):0},
                        'NOR': {(0,0):1, (0,1):0, (1,0):0, (1,1):0, (0,):1, (1,):0},
                        'XOR': {(0,0):0, (0,1):1, (1,0):1, (1,1):0, (0,):0, (1,):0},
                        'XNOR': {(0,0):1, (0,1):0, (1,0):0, (1,1):1, (0,):1, (1,):1}
                      }
        return truth_table[type]





# generate a circuit
class Circuit:
    def __init__(self,json_circuit):
        self.gates, self.wires = Circuit.generate_circuit(json_circuit)
        self.inputs = len(json_circuit['alice'] + json_circuit.get('bob',[]))
        self.alice = json_circuit['alice']
        self.bob = json_circuit.get('bob',[])
        self.output = json_circuit['out']
        self.name = json_circuit['name']
        self.garbled_truth_table = Circuit.generate_garbled_truth_table(self.gates, self.wires, self.output)

    def generate_circuit(json_circuit):
        gates = []
        wires = []

        for gate in json_circuit['gates']:
            gates.append(Gate(gate['in'], gate['id'], gate['type']))
            for wire in gate['in']:
                wires.append(Wire(wire, gate['id']))

        for wire in json_circuit['out']:
            wires.append(Wire(wire, None))

        return gates, wires

    def generate_garbled_truth_table(gates, wires, outputs):
        output_wires = []
        for output in outputs:
            output_wires.append(util.find_wire(output, wires))

        garbled_table = {}
        for gate in gates:
            gate_id = gate.output
            num_gate_inputs = 1 if gate.type == 'NOT' else 2
            perms = util.generate_perms(num_gate_inputs)
            for perm in perms:
                wire_0 = util.find_wire(gate.inputs[0], wires)
                useful_value_0 = wire_0.p_bit ^ int(perm[0])
                wire_1 = util.find_wire(gate.inputs[1], wires)
                useful_value_1 = wire_1.p_bit ^ int(perm[1])
                result = gate.truth_table[(useful_value_0, useful_value_1)]

                output = output_wires[0]
                output_key = output.key_1 if bool(result) else output.key_0

                output_val =  result ^ output.p_bit

                encryption_key_0 = wire_0.key_1 if bool(useful_value_0) else wire_0.key_0

                encryption_key_1 = wire_1.key_1 if bool(useful_value_1) else wire_1.key_0

                f = Fernet(encryption_key_0)
                print(type(output_key))
                one_pass_encryption = f.encrypt(output_key + bytes(output_val))
                f = Fernet(encryption_key_1)
                two_pass_encryption = f.encrypt(one_pass_encryption)
                encryptions = garbled_table.get(gate_id, {})
                encryptions[perm] = two_pass_encryption
                garbled_table[gate_id] = encryptions
                # garbled_table[gate_id][perm] = two_pass_encryption

        print(garbled_table)












            # print(perms)




    # def find_sink(wire, gates):
    #     for gate in gates:
    #         if wire in gate.inputs:
    #             return gate.output
    #
    #     return None


    def garble(circuit):
        circuit.gates[0].inputs = ()
        for gate in circuit.gates:
            gate.output = gate.truth_table[gate.inputs]
