
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import math

class Wire:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink
        self.value = -1

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
                        'XNOR': {(0,0):1, (0,1):0, (1,0):0, (1,1):0, (0,):1, (1,):1}
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
