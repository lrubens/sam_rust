import argparse
import sys
from process_funcs import *
from google.protobuf import text_format

import tortilla_pb2
import comal_pb2


def insert_broadcast(program, map_broad, map_channel_broadcast, max_node_id, max_channel_id):
    for (key, val) in map_channel_broadcast.items():
        if key == 0:
            continue
        new_broadcast = program.operators.add(
            name="broadcast", id=max_node_id+1)
        outputs = []
        if val[1] == "crd":
            new_broadcast.broadcast.crd.input.id.id = key
            new_broadcast.broadcast.crd.input.name = val[1]
            outputs = new_broadcast.broadcast.crd.outputs
        if val[1] == "ref":
            new_broadcast.broadcast.ref.input.id.id = key
            new_broadcast.broadcast.ref.input.name = val[1]
        if val[1] == "val":
            new_broadcast.broadcast.val.input.id.id = key
            new_broadcast.broadcast.val.input.name = val[1]
        if val[1] == "repsig":
            new_broadcast.broadcast.repsig.input.id.id = key
            new_broadcast.broadcast.repsig.input.name = val[1]

        for s_id in map_broad[(key, val[1])]:
            s_id.id.id = max_channel_id + 1
            outputs.add().id.id = max_channel_id + 1
            max_channel_id += 1
        max_node_id += 1


def register_process_funcs(process_funcs):
    process_funcs["fiber_lookup"] = process_fiber_lookup
    process_funcs["repeat"] = process_repeat
    process_funcs["repeatsig"] = process_repeat_sig
    process_funcs["fiber_write"] = process_fiber_write
    process_funcs["val_write"] = process_val_write
    process_funcs["array"] = process_array
    process_funcs["joiner"] = process_joiner
    process_funcs["reduce"] = process_reduce
    process_funcs["alu"] = process_alu
    process_funcs["coord_drop"] = process_coord_drop
    process_funcs["coord_hold"] = process_coord_hold
    process_funcs["spacc"] = process_spacc


def parse_proto(proto_file, out_bin):
    program = tortilla_pb2.ProgramGraph()

    with open(proto_file, "rb") as f:
        proto_fd = f.read()
        text_format.Parse(proto_fd, program)
    program_name = program.name
    operators = program.operators

    process_funcs = {}
    register_process_funcs(process_funcs)

    max_node_id = 0
    max_channel_id = 0
    map_broad = {}
    map_channel_broadcast = {}

    for operator in operators:
        op = operator.WhichOneof("op")
        op_id = operator.id
        max_node_id = max(max_node_id, op_id)
        max_id = process_funcs[op](operator, map_broad, map_channel_broadcast)
        max_channel_id = max(max_channel_id, max_id)

    insert_broadcast(program, map_broad, map_channel_broadcast,
                     max_node_id, max_channel_id)

    comal_graph = comal_pb2.ComalGraph()
    comal_graph.name = "comal graph"
    comal_graph.channel_size = 1024
    comal_graph.graph.CopyFrom(program)

    # out_comal = "comal.pbtxt"
    # with open(out_comal, "w") as f:
    #     text_format.PrintMessage(comal_graph, f)

    with open(out_bin, "wb") as f:
        f.write(comal_graph.SerializeToString())


def merge_protos(proto_files, out_bin):
    # program1 = tortilla_pb2.ProgramGraph()
    # program2 = tortilla_pb2.ProgramGraph()
    program_graphs = []

    for i, proto in enumerate(proto_files):
        program_graph = tortilla_pb2.ProgramGraph()
        with open(proto_files[i], "rb") as f:
            proto_fd = f.read()
            text_format.Parse(proto_fd, program_graph)
        program_graphs.append(program_graph)

    process_funcs = {}
    register_process_funcs(process_funcs)

    max_node_ids = []
    max_channel_ids = []
    map_broad = {}
    map_channel_broadcast = {}

    index_variables = []
    for i, program in enumerate(program_graphs):
        ind = []
        max_node_ids.append(0)
        max_channel_ids.append(0)
        for operator in program.operators:
            op = operator.WhichOneof("op")
            op_id = operator.id
            max_node_ids[i] = max(max_node_ids[i], op_id)
            if op == "fiber_lookup":
                index = operator.fiber_lookup.index
                if not ind or (ind and ind[len(ind) - 1] is not index):
                    ind.append(index)
                max_channel_ids[i] = max(
                    max_channel_ids[i], operator.fiber_lookup.output_ref.id.id)
            if op == "fiber_write":
                print("")
        index_variables.append(ind)

    shared_vars = [i[0] for i in zip(*index_variables)]

    print(max_channel_ids)
    print(max_node_ids)

    new_program_graph = tortilla_pb2.ProgramGraph()

    # for programs in program_graphs:
    #     ind = []
    max_node_id = sum(max_node_ids)
    max_channel_id = sum(max_channel_ids)
    for i, operator in enumerate(program_graphs[0].operators):
        operator2 = program_graphs
        op = operator.WhichOneof("op")
        op_id = operator.id
        new_program_graph.operators.add().CopyFrom(operator)
        new_program_graph.operators[-1].id = max_node_id
        max_node_id -= 1

    print(new_program_graph)

    # for operator in operators1:
    #     op = operator.WhichOneof("op")
    #     op_id = operator.id
    #     max_node_id = max(max_node_id, op_id)
    #     max_id = process_funcs[op](operator, map_broad, map_channel_broadcast)
    #     max_channel_id = max(max_channel_id, max_id)

    # insert_broadcast(program1, map_broad, map_channel_broadcast,
    #                  max_node_id, max_channel_id)

    # comal_graph = comal_pb2.ComalGraph()
    # comal_graph.name = "comal graph"
    # comal_graph.channel_size = 1024
    # comal_graph.graph.CopyFrom(program1)

    # out_comal = "comal.pbtxt"
    # with open(out_comal, "w") as f:
    #     text_format.PrintMessage(comal_graph, f)

    # with open(out_bin, "wb") as f:
    #     f.write(comal_graph.SerializeToString())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Comal Adapter",
                                     description="Applies optimizations and adds metadata to program graph")
    parser.add_argument('-p', '--proto_file', type=str, nargs='*',
                        help='path of the textproto file')
    parser.add_argument('-o', '--out_bin',
                        help='path of the output comal graph file')
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    if type(args.proto_file) == list:
        merge_protos(args.proto_file, args.out_bin)
    else:
        parse_proto(args.proto_file, args.out_bin)
