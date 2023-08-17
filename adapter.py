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
    expr_tens = []
    for i, program in enumerate(program_graphs):
        ind = []
        max_node_ids.append(0)
        max_channel_ids.append(0)
        expr_tens.append([expr.split("=")[0] for expr in program.name.strip("\"").split(",")])
        print(expr_tens)
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
            # if op == "fiber_write":
            #     print("")
        index_variables.append(ind)

    # TODO: Figure out how to get dependencies between each expression
    shared_tens = [i[0] for i in zip(*expr_tens)]
    dependencies = {expr_num: shared_tens[0] for expr_num in range(1, len(program_graphs))}
    shared_vars = [i[0] for i in zip(*index_variables)]

    new_program_graph = tortilla_pb2.ProgramGraph()

    max_node_id = sum(max_node_ids)
    max_channel_id = sum(max_channel_ids)

    interm_outs = {}

    for i, program_graph in enumerate(program_graphs):
        chan_map = {}
        for operator in program_graph.operators:
            op_id = operator.id
            max_node_id -= 1
            # op = new_program_graph.operators[-1].WhichOneof("op")
            op = operator.WhichOneof("op")
            # operator = new_program_graph.operators[-1]
            if op == "fiber_lookup":
                if i in dependencies and operator.fiber_lookup.tensor in shared_tens:
                    continue
                in1 = operator.fiber_lookup.input_ref.id.id
                if in1 not in chan_map and in1 != 0:
                    chan_map[in1] = max_channel_id
                    operator.fiber_lookup.input_ref.id.id = max_channel_id
                    max_channel_id -= 1
                elif in1 == 0:
                    chan_map[in1] = in1
                elif in1 != 0:
                    operator.fiber_lookup.input_ref.id.id = chan_map[in1]
                # in1 = operator.fiber_lookup.input_ref.id.id
                if (chan_map[in1], "ref") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in1], 1, "ref")
                else:
                    map_broad[(chan_map[in1], "ref")] = []
                
                out1 = operator.fiber_lookup.output_ref.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.fiber_lookup.output_ref.id.id = max_channel_id
                    max_channel_id -= 1
                elif out1 != 0:
                    operator.fiber_lookup.output_ref.id.id = chan_map[out1]
                out2 = operator.fiber_lookup.output_crd.id.id
                if out2 not in chan_map and out2 != 0:
                    chan_map[out2] = max_channel_id
                    operator.fiber_lookup.output_crd.id.id = max_channel_id
                    max_channel_id -= 1
                elif out2 != 0:
                    operator.fiber_lookup.output_crd.id.id = chan_map[out2]
                map_broad[(chan_map[in1], "ref")].append(operator.fiber_lookup.input_ref)

                if i not in dependencies:
                    if operator.fiber_lookup.index in shared_vars:
                        interm_outs[(operator.fiber_lookup.index, "crd")] = operator.fiber_lookup.output_crd
                        interm_outs[(operator.fiber_lookup.index, "ref")] = operator.fiber_lookup.output_ref
            elif op == "repeat":
                in1 = operator.repeat.input_rep_sig.id.id
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.repeat.input_rep_sig.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.repeat.input_rep_sig.id.id = chan_map[in1]

                in2 = operator.repeat.input_ref.id.id
                if in2 not in chan_map and in2 != 0:
                    chan_map[in2] = max_channel_id
                    operator.repeat.input_ref.id.id = max_channel_id
                    max_channel_id -= 1
                elif in2 == 0:
                    chan_map[in2] = in2
                elif in2 != 0:
                    operator.repeat.input_ref.id.id = chan_map[in2] 

                if (chan_map[in1], "repsig") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in1], 1, "repsig")
                else:
                    map_broad[(chan_map[in1], "repsig")] = []

                if (chan_map[in2], "ref") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in2], 1, "ref")
                else:
                    map_broad[(chan_map[in2], "ref")] = []

                map_broad[(chan_map[in1], "repsig")].append(operator.repeat.input_rep_sig)
                map_broad[(chan_map[in2], "ref")].append(operator.repeat.input_ref)

                out1 = operator.repeat.output_ref.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.repeat.output_ref.id.id = max_channel_id
                    max_channel_id -= 1
            elif op == "joiner":
                in1 = operator.joiner.input_pairs[0].crd.id.id
                in2 = operator.joiner.input_pairs[0].ref.id.id
                in3 = operator.joiner.input_pairs[1].crd.id.id
                in4 = operator.joiner.input_pairs[1].ref.id.id

                tensor_1 = operator.joiner.input_pairs[0].crd.name[-1]
                tensor_2 = operator.joiner.input_pairs[1].crd.name[-1]

                if i in dependencies and tensor_1 in shared_tens:
                    chan_map[in1] = interm_outs[(operator.joiner.index, "crd")].id.id
                    chan_map[in2] = interm_outs[(operator.joiner.index, "ref")].id.id
                elif i in dependencies and tensor_2 in shared_tens:
                    chan_map[in3] = interm_outs[(operator.joiner.index, "crd")].id.id
                    chan_map[in4] = interm_outs[(operator.joiner.index, "ref")].id.id
                    
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.joiner.input_pairs[0].crd.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.joiner.input_pairs[0].crd.id.id = chan_map[in1]
                if in2 not in chan_map:
                    chan_map[in2] = max_channel_id
                    operator.joiner.input_pairs[0].ref.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.joiner.input_pairs[0].ref.id.id = chan_map[in2]
                if in3 not in chan_map:
                    chan_map[in3] = max_channel_id
                    operator.joiner.input_pairs[1].crd.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.joiner.input_pairs[1].crd.id.id = chan_map[in3]
                if in4 not in chan_map:
                    chan_map[in4] = max_channel_id
                    operator.joiner.input_pairs[1].ref.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.joiner.input_pairs[1].ref.id.id = chan_map[in4]
                if (chan_map[in1], "crd") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in1], 1, "crd")
                else:
                    map_broad[(chan_map[in1], "crd")] = []
                if (chan_map[in2], "ref") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in2], 1, "ref")
                else:
                    map_broad[(chan_map[in2], "ref")] = []
                if (chan_map[in3], "crd") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in3], 1, "crd")
                else:
                    map_broad[(chan_map[in3], "crd")] = []
                if (chan_map[in4], "ref") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in4], 1, "ref")
                else:
                    map_broad[(chan_map[in4], "ref")] = []

                map_broad[(chan_map[in1], "crd")].append(operator.joiner.input_pairs[0].crd)
                map_broad[(chan_map[in2], "ref")].append(operator.joiner.input_pairs[0].ref)
                map_broad[(chan_map[in3], "crd")].append(operator.joiner.input_pairs[1].crd)
                map_broad[(chan_map[in4], "ref")].append(operator.joiner.input_pairs[1].ref)
                
                out1 = operator.joiner.output_ref1.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.joiner.output_ref1.id.id = max_channel_id
                    max_channel_id -= 1
                    
                out2 = operator.joiner.output_ref2.id.id
                if out2 not in chan_map and out2 != 0:
                    chan_map[out2] = max_channel_id
                    operator.joiner.output_ref2.id.id = max_channel_id
                    max_channel_id -= 1
                    
                out3 = operator.joiner.output_crd.id.id
                if out3 not in chan_map and out3 != 0:
                    chan_map[out3] = max_channel_id
                    operator.joiner.output_crd.id.id = max_channel_id
                    max_channel_id -= 1

                if i not in dependencies:
                    tensor_1 = operator.joiner.input_pairs[0].crd.name[-1]
                    tensor_2 = operator.joiner.input_pairs[1].crd.name[-1]
                    if operator.fiber_lookup.index in shared_vars:
                        out_crd = ""
                        out_ref = ""
                        # out_crd = operator.joiner.input_pairs[0].crd if tensor_1 in shared_tens else 
                        if tensor_1 in shared_tens:
                            out_crd = operator.joiner.input_pairs[0].crd
                            out_ref = operator.joiner.input_pairs[0].ref
                        elif tensor_2 in shared_tens:
                            out_crd = operator.joiner.input_pairs[1].crd
                            out_ref = operator.joiner.input_pairs[1].ref
                        interm_outs[(operator.fiber_lookup.index, "crd")] = out_crd
                        interm_outs[(operator.fiber_lookup.index, "ref")] = out_ref
            elif op == "repeatsig":
                in1 = operator.repeatsig.input_crd.id.id
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.repeatsig.input_crd.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.repeatsig.input_crd.id.id = chan_map[in1]
                if (chan_map[in1], "crd") in map_broad:
                    set_or_create(map_channel_broadcast, chan_map[in1], 1, "crd")
                else:
                    map_broad[(chan_map[in1], "crd")] = []
                map_broad[(chan_map[in1], "crd")].append(operator.repeatsig.input_crd)

                out1 = operator.repeatsig.output_rep_sig.id.id
                if out1 not in chan_map:
                    chan_map[out1] = max_channel_id
                    operator.repeatsig.output_rep_sig.id.id = max_channel_id
                    max_channel_id -= 1
            elif op == "val_write":
                in1 = operator.val_write.input_val.id.id
                if i not in dependencies:
                    interm_outs[(operator.val_write.tensor, "val")] = operator.val_write.input_val
                    continue
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.val_write.input_val.id.id = max_channel_id
                    max_channel_id -= 1
                else:
                    operator.val_write.input_val.id.id = chan_map[in1]
                if (chan_map[in1], "val") in map_broad:
                    set_or_create(map_channel_broadcast, in1, 1, "val")
                else:
                    map_broad[(chan_map[in1], "val")] = []
                map_broad[(chan_map[in1], "val")].append(operator.fiber_write.input_crd)

            new_program_graph.operators.add().CopyFrom(operator)
            new_program_graph.operators[-1].id = max_node_id
    
    print(interm_outs)
                

    

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
