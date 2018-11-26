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
        # load all the circuits in the file
        json_circuits = json.load(json_file)

    # iterate through circuits
    for json_circuit in json_circuits['circuits']:
        # parse new circuit
        circuit = Circuit(json_circuit)
        # calculate number of permutations based on number of inputs
        perms = util.generate_perms(circuit.inputs)

        print("\n======= " + circuit.name + " =======")

        # tell bob input lengths so it know how many times to run
        socket.send((len(circuit.bob), len(circuit.alice)))
        socket.receive()
        for perm in perms:
            # create new garbled circuit for each permutation
            circuit = Circuit(json_circuit)
            gates = circuit.gates
            wires = circuit.wires
            # save wires to use for OT late
            saved_wires = copy.deepcopy(wires)

            wires.sort(key=lambda x: x.source)
            # set value key pair for Alice inputs
            for input_wire_source, value in zip(circuit.alice, perm):
                # set all input wires to value
                for wire in wires:
                    if wire.source == input_wire_source:
                        value = int(value)
                        key = wire.key_1 if value == 1 else wire.key_0
                        # print(value)
                        ext_value = value ^ wire.p_bit
                        wire.value = (key, ext_value)

            # redact circuits and gates
            circuit.gates = util.redact_gates(circuit.gates)
            circuit.wires = util.redact_wires(circuit.wires)
            circuit.name = None
            # send Bob redacted circuit
            socket.send(circuit)
            socket.receive()
            # OT for Bob's input keys and values
            for w in circuit.bob:
                full_wire = util.find_wire(w, saved_wires)
                ot_alice(socket, (full_wire.key_0, 0 ^ full_wire.p_bit), (full_wire.key_1, 1 ^ full_wire.p_bit))

            socket.send('send output')
            # receive and print Bob's evaluation result
            output_values = socket.receive()
            util.print_output(perm, output_values, circuit.alice, circuit.bob, circuit.output)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
    socket = util.ServerSocket()
    util.log(f'Bob: Listening ...')
    while True:
        # work out number of times to run Bob and set up looks
        (bob_len, alice_len) = socket.receive()
        socket.send('thanks')
        perms = util.generate_perms(bob_len)

        for i in range(2 ** alice_len):
            for perm in perms:
                # receive circuit
                circuit = socket.receive()
                socket.send('thanks')
                gates = circuit.gates
                wires = circuit.wires
                garbled_truth_table = circuit.garbled_truth_table

                # Work out Bob's input wires
                for input_wire_source, value in zip(circuit.bob, perm):
                    # set all input wires to value
                    for wire in wires:
                        if wire.source == input_wire_source:
                            # OT to get key and values for Bob's inputs
                            wire.value = ot_bob(socket, value)

                # evaluate gates
                for gate in gates:
                    inputs = util.find_input_values(gate.inputs, wires)
                    ext_values = ''
                    decrypt_keys = []
                    # extract keys and values from input wire
                    for input in gate.inputs:
                        wire = util.find_wire(input, wires)
                        decrypt_keys.append(wire.value[0])
                        ext_values += str(wire.value[1])

                    # Check if 1 or 2 input gate and decrypts garbled table entry
                    output = None
                    if len(gate.inputs) != 1:
                        double_enc_key = garbled_truth_table[gate.output][ext_values]
                        f = Fernet(decrypt_keys[1])
                        single_enc_key = f.decrypt(double_enc_key)
                    else:
                        single_enc_key = garbled_truth_table[gate.output][ext_values]

                    f = Fernet(decrypt_keys[0])
                    output = f.decrypt(single_enc_key)

                    # find output wire and set its key value pair
                    output_wire = util.find_wire(gate.output, wires)
                    output_wire.value = util.partition_to_tuple(output)

                # xor p-bit with circuit output value and return evaluation result to Alice
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
