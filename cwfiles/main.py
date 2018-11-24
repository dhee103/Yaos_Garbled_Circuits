
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import json	# load
import sys	# argv

import ot	# alice, bob
import util	# ClientSocket, log, ServerSocket
from yao import *	# Circuit


# Alice is the circuit generator (client) __________________________________

def alice(filename):
  socket = util.ClientSocket()

  with open(filename) as json_file:
    json_circuits = json.load(json_file)

  for json_circuit in json_circuits['circuits']:
    circuit = Circuit(json_circuit)
    gates = circuit.gates
    wires = circuit.wires

    perms = util.generate_perms(circuit.inputs)

    wires.sort(key=lambda x: x.source)

    print(circuit.name)
    for perm in perms:
        for input_wire_source,value in zip(circuit.alice + circuit.bob, perm):
            # set all input wires to value
            for wire in wires:
                if wire.source == input_wire_source:
                    wire.value = int(value)

        output_values = []

        for gate in gates:
            inputs = util.find_input_values(gate.inputs,wires)
            # find wire whose source is gate output_wire
            wire = util.find_wire(gate.output,wires)
            wire.value = gate.truth_table[inputs]
            if wire.source in circuit.output:
                output_values.append(wire.value)

        util.print_output(perm, output_values, circuit.alice, circuit.bob, circuit.output)

    # perm = '10101'
    # for input_wire_source,value in zip(circuit.alice + circuit.bob, perm):
    #     # set all input wires to value
    #     for wire in wires:
    #         if wire.source == input_wire_source:
    #             wire.value = int(value)
    #
    # for wire in wires:
    #     print(wire)
    # for gate in gates:
    #     print(gate)
    #
    # for gate in gates:
    #     inputs = util.find_input_values(gate.inputs,wires)
    #     # find wire whose source is gate output_wire
    #     print(gate.output)
    #     wire = util.find_wire(gate.output,wires)
    #     wire.value = gate.truth_table[inputs]

    # util.print_output(perm, wire.value, circuit.alice, circuit.bob, circuit.output)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
  socket = util.ServerSocket()
  util.log(f'Bob: Listening ...')
  while True:
    # << removed >>
    pass

# local test of circuit generation and evaluation, no transfers_____________

def local_test(filename):
  with open(filename) as json_file:
    json_circuits = json.load(json_file)

  for json_circuit in json_circuits['circuits']:
    circuit = Circuit(json_circuit)
    # print(Circuit.garble(circuit))
    # print(circuit.wires)


# main _____________________________________________________________________

def main():
  behaviour = sys.argv[1]
  if   behaviour == 'alice': alice(filename=sys.argv[2])
  elif behaviour == 'bob':   bob()
  elif behaviour == 'local': local_test(filename=sys.argv[2])

if __name__ == '__main__':
  main()

# __________________________________________________________________________
