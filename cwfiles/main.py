# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import json  # load
import sys  # argv
import pickle
import ot  # alice, bob
import util  # ClientSocket, log, ServerSocket
from yao import *  # Circuit
from ot import *
import copy


# Alice is the circuit generator (client) __________________________________

def alice(filename):
    socket = util.ClientSocket()

    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        circuit = Circuit(json_circuit)
        perms = util.generate_perms(circuit.inputs)

        print("\n======= " + circuit.name + " =======")

        socket.send((len(circuit.bob), len(circuit.alice)))
        socket.receive()
        for perm in perms:
            circuit = Circuit(json_circuit)
            gates = circuit.gates
            wires = circuit.wires
            saved_wires = copy.deepcopy(wires)

            garbled_truth_table = circuit.garbled_truth_table
            wires.sort(key=lambda x: x.source)
            for input_wire_source, value in zip(circuit.alice , perm):
                # set all input wires to value
                for wire in wires:
                    if wire.source == input_wire_source:
                        value = int(value)
                        key = wire.key_1 if value == 1 else wire.key_0
                        # print(value)
                        ext_value = value ^ wire.p_bit
                        wire.value = (key, ext_value)

            circuit.gates = util.redact_gates(circuit.gates)
            circuit.wires = util.redact_wires(circuit.wires)
            circuit.name = None
            socket.send(circuit)
            socket.receive()
            for w in circuit.bob:
                full_wire = util.find_wire(w, saved_wires)
                ot_alice(socket, (full_wire.key_0, 0 ^ full_wire.p_bit), (full_wire.key_1, 1 ^ full_wire.p_bit))

            socket.send('send output')
            output_values = socket.receive()
            util.print_output(perm, output_values, circuit.alice, circuit.bob, circuit.output)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
    socket = util.ServerSocket()
    util.log(f'Bob: Listening ...')
    while True:
        (bob_len, alice_len) = socket.receive()
        socket.send('thanks')
        perms = util.generate_perms(bob_len)

        for i in range(2**alice_len):
            for perm in perms:
                circuit = socket.receive()
                socket.send('thanks')
                gates = circuit.gates
                wires = circuit.wires
                garbled_truth_table = circuit.garbled_truth_table

                for input_wire_source, value in zip(circuit.bob, perm):
                    # set all input wires to value
                    for wire in wires:
                        if wire.source == input_wire_source:
                            wire.value = ot_bob(socket, value)

                for gate in gates:
                    inputs = util.find_input_values(gate.inputs, wires)
                    ext_values = ''
                    decrypt_keys = []
                    for input in gate.inputs:
                        wire = util.find_wire(input, wires)
                        decrypt_keys.append(wire.value[0])
                        ext_values += str(wire.value[1])

                    output = None
                    if len(gate.inputs) != 1:
                        double_enc_key = garbled_truth_table[gate.output][ext_values]
                        f = Fernet(decrypt_keys[1])
                        single_enc_key = f.decrypt(double_enc_key)
                    else:
                        single_enc_key = garbled_truth_table[gate.output][ext_values]

                    f = Fernet(decrypt_keys[0])
                    output = f.decrypt(single_enc_key)

                    output_wire = util.find_wire(gate.output, wires)
                    output_wire.value = util.partition_to_tuple(output)

                output_values = []
                for output in circuit.output:
                    wire = util.find_wire(output, wires)
                    if wire.source in circuit.output:
                        output_values.append(wire.value[1] ^ wire.p_bit)
                socket.receive()
                socket.send(output_values)



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
    if behaviour == 'alice':
        alice(filename=sys.argv[2])
    elif behaviour == 'bob':
        bob()
    elif behaviour == 'local':
        local_test(filename=sys.argv[2])


if __name__ == '__main__':
    main()

# __________________________________________________________________________
