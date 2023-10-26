import argparse
import sys
from process_funcs import *
from google.protobuf import text_format

import tortilla_pb2
import comal_pb2
import itertools
import copy


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
            outputs = new_broadcast.broadcast.ref.outputs
        if val[1] == "val":
            new_broadcast.broadcast.val.input.id.id = key
            new_broadcast.broadcast.val.input.name = val[1]
            outputs = new_broadcast.broadcast.val.outputs
        if val[1] == "repsig":
            new_broadcast.broadcast.repsig.input.id.id = key
            new_broadcast.broadcast.repsig.input.name = val[1]
            outputs = new_broadcast.broadcast.repsig.outputs

        for s_id in map_broad[(key, val[1])]:
            s_id.id.id = max_channel_id + 1
            outputs.add().id.id = max_channel_id + 1
            max_channel_id += 1
        max_node_id += 1


def add_void_channels(program, input_id_lst):
    for operator in program.operators:
        op = operator.WhichOneof("op")
        op_id = operator.id
        if op == "fiber_lookup":
            out1 = operator.fiber_lookup.output_ref
            if out1.id.id not in input_id_lst:
                out1.id.id = 0
        elif op == "repeat":
            out1 = operator.repeat.output_ref
            if out1.id.id not in input_id_lst:
                out1.id.id = 0
        elif op == "joiner":
            out1 = operator.joiner.output_refs[0]
            out2 = operator.joiner.output_refs[1]
            out3 = operator.joiner.output_crd
            if out1.id.id not in input_id_lst:
                out1.id.id = 0
            if out2.id.id not in input_id_lst:
                out2.id.id = 0
            if out3.id.id not in input_id_lst:
                out3.id.id = 0
        elif op == "repeatsig":
            out1 = operator.repeatsig.output_rep_sig
            if out1.id.id not in input_id_lst:
                out1.id.id = 0
        elif op == "reduce":
            out1 = operator.reduce.output_val
            if out1.id.id not in input_id_lst:
                out1.id.id = 0
        elif op == "coord_drop":
            out1 = operator.coord_drop.output_inner_crd
            out2 = operator.coord_drop.output_outer_crd

            if out1.id.id not in input_id_lst:
                out1.id.id = 0
            if out2.id.id not in input_id_lst:
                out2.id.id = 0


def register_process_funcs(process_funcs):
    process_funcs["root"] = process_root
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

    # merge_elementwise(proto_file, "relu", out_bin)

    max_node_id = 0
    max_channel_id = 0
    map_broad = {}
    map_channel_broadcast = {}
    out_lst = []

    for operator in operators:
        op = operator.WhichOneof("op")
        op_id = operator.id
        max_node_id = max(max_node_id, op_id)
        max_id = process_funcs[op](
            operator, map_broad, map_channel_broadcast, out_lst)
        max_channel_id = max(max_channel_id, max_id)

    input_id_lst = [s[0].id.id for s in map_broad.values()]
    add_void_channels(program, input_id_lst)

    insert_broadcast(program, map_broad, map_channel_broadcast,
                     max_node_id, max_channel_id)

    comal_graph = comal_pb2.ComalGraph()
    comal_graph.name = "comal graph"
    comal_graph.channel_size = 1024
    comal_graph.graph.CopyFrom(program)

    out_comal = "comal.pbtxt"
    with open(out_comal, "w") as f:
        text_format.PrintMessage(comal_graph, f)

    with open(out_bin, "wb") as f:
        f.write(comal_graph.SerializeToString())


def merge_elementwise(proto_file, op_name, out_bin):
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
        if op == "val_write":
            intrin = program.operators.add(
                name=op_name, id=max_node_id+1)
            intrin.func.name = op_name
            intrin.func.input_val.id.id = operator.val_write.input_val.id.id
            intrin.func.input_val.name = operator.val_write.input_val.name
            intrin.func.output_val.id.id = max_channel_id + 1
            operator.val_write.input_val.id.id = max_channel_id + 1
        if op == "func":
            continue

        max_id = process_funcs[op](operator, map_broad, map_channel_broadcast)
        max_channel_id = max(max_channel_id, max_id)

    input_id_lst = [s[0].id.id for s in map_broad.values()]
    add_void_channels(program, input_id_lst)

    insert_broadcast(program, map_broad, map_channel_broadcast,
                     max_node_id, max_channel_id)

    comal_graph = comal_pb2.ComalGraph()
    comal_graph.name = "comal graph"
    comal_graph.channel_size = 1024
    comal_graph.graph.CopyFrom(program)

    # out_comal = "comal.pbtxt"
    # with open(out_comal, "w") as f:
    #     text_format.PrintMessage(comal_graph, f)

    print(comal_graph)

    # with open(out_bin, "wb") as f:
    #     f.write(comal_graph.SerializeToString())


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
    new_name = ""
    expr = {}
    repsiggen = {}
    for i, program in enumerate(program_graphs):
        ind = []
        max_node_ids.append(0)
        max_channel_ids.append(0)
        expr_tens.append([expr.split("=")[0]
                         for expr in program.name.strip("\"").split(",")])
        new_name = program.name.strip("\"").split(",")
        expr[new_name[0]] = new_name[1:]
        print(expr)
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
        index_variables.append(ind)

    final_expr = []
    for i in expr[list(expr.keys())[-1]]:
        if i in expr:
            final_expr.append(",".join(expr[i]))
        else:
            final_expr.append(i)
    final_name = list(expr.keys())[-1] + "," + \
        ",".join(final_expr)
    print(final_name)

    # TODO: Figure out how to get dependencies between each expression
    shared_tens = [i[0] for i in zip(*expr_tens)]
    dependencies = {expr_num: shared_tens[0]
                    for expr_num in range(1, len(program_graphs))}
    shared_vars = [i[0] for i in zip(*index_variables)]

    new_program_graph = tortilla_pb2.ProgramGraph()

    new_program_graph.name = final_name

    # max_node_id = sum(max_node_ids)
    # max_channel_id = sum(max_channel_ids)

    max_node_id = 1
    max_channel_id = 1

    interm_outs = {}

    for i, program_graph in enumerate(program_graphs):
        tensor_to_chan = {}
        chan_map = {}
        for operator in program_graph.operators:
            op_id = operator.id
            max_node_id += 1
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
                    print(max_channel_id)
                    max_channel_id += 1
                elif in1 == 0:
                    chan_map[in1] = in1
                elif in1 != 0:
                    operator.fiber_lookup.input_ref.id.id = chan_map[in1]
                # inputs_lst.append(cha)
                # in1 = operator.fiber_lookup.input_ref.id.id
                if (chan_map[in1], "ref") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "ref")
                else:
                    map_broad[(chan_map[in1], "ref")] = []

                out1 = operator.fiber_lookup.output_ref.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.fiber_lookup.output_ref.id.id = max_channel_id
                    # print(max_channel_id)
                    max_channel_id += 1
                elif out1 != 0:
                    operator.fiber_lookup.output_ref.id.id = chan_map[out1]
                out2 = operator.fiber_lookup.output_crd.id.id
                if out2 not in chan_map and out2 != 0:
                    chan_map[out2] = max_channel_id
                    operator.fiber_lookup.output_crd.id.id = max_channel_id
                    max_channel_id += 1
                elif out2 != 0:
                    operator.fiber_lookup.output_crd.id.id = chan_map[out2]

                if i not in dependencies:
                    if operator.fiber_lookup.index in shared_vars:
                        interm_outs[(operator.fiber_lookup.index, "crd")
                                    ] = operator.fiber_lookup.output_crd.id.id
                        interm_outs[(operator.fiber_lookup.index, "ref")
                                    ] = operator.fiber_lookup.output_ref.id.id

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "ref")].append(
                    new_operator.fiber_lookup.input_ref)

            elif op == "repeat":
                if i in dependencies and operator.repeat.tensor in shared_tens:
                    continue
                repeat_index = operator.repeat.index
                if repeat_index in repsiggen:
                    in1 = repsiggen[repeat_index].output_rep_sig.id.id
                    print(in1, repeat_index, operator.repeat.tensor)
                    chan_map[in1] = in1
                    max_channel_id += 1
                else:
                    in1 = operator.repeat.input_rep_sig.id.id

                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.repeat.input_rep_sig.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.repeat.input_rep_sig.id.id = chan_map[in1]

                in2 = operator.repeat.input_ref.id.id
                if in2 not in chan_map and in2 != 0:
                    chan_map[in2] = max_channel_id
                    operator.repeat.input_ref.id.id = max_channel_id
                    max_channel_id += 1
                elif in2 == 0:
                    chan_map[in2] = in2
                elif in2 != 0:
                    operator.repeat.input_ref.id.id = chan_map[in2]

                if (chan_map[in1], "repsig") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "repsig")
                else:
                    map_broad[(chan_map[in1], "repsig")] = []

                if (chan_map[in2], "ref") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in2], 1, "ref")
                else:
                    map_broad[(chan_map[in2], "ref")] = []

                out1 = operator.repeat.output_ref.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.repeat.output_ref.id.id = max_channel_id
                    max_channel_id += 1
                elif out1 != 0:
                    operator.repeat.output_ref.id.id = chan_map[out1]

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "repsig")].append(
                    new_operator.repeat.input_rep_sig)
                map_broad[(chan_map[in2], "ref")].append(
                    new_operator.repeat.input_ref)

            elif op == "joiner":
                in1 = operator.joiner.input_pairs[0].crd.id.id
                in2 = operator.joiner.input_pairs[0].ref.id.id
                in3 = operator.joiner.input_pairs[1].crd.id.id
                in4 = operator.joiner.input_pairs[1].ref.id.id

                tensor_1 = operator.joiner.input_pairs[0].crd.name[-1]
                tensor_2 = operator.joiner.input_pairs[1].crd.name[-1]

                if i in dependencies and tensor_1 in shared_tens:
                    chan_map[in1] = interm_outs[(operator.joiner.index, "crd")]
                    chan_map[in2] = interm_outs[(operator.joiner.index, "ref")]
                elif i in dependencies and tensor_2 in shared_tens:
                    chan_map[in3] = interm_outs[(operator.joiner.index, "crd")]
                    chan_map[in4] = interm_outs[(operator.joiner.index, "ref")]

                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.joiner.input_pairs[0].crd.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.joiner.input_pairs[0].crd.id.id = chan_map[in1]
                if in2 not in chan_map:
                    chan_map[in2] = max_channel_id
                    operator.joiner.input_pairs[0].ref.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.joiner.input_pairs[0].ref.id.id = chan_map[in2]
                if in3 not in chan_map:
                    chan_map[in3] = max_channel_id
                    operator.joiner.input_pairs[1].crd.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.joiner.input_pairs[1].crd.id.id = chan_map[in3]
                if in4 not in chan_map:
                    chan_map[in4] = max_channel_id
                    operator.joiner.input_pairs[1].ref.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.joiner.input_pairs[1].ref.id.id = chan_map[in4]
                if (chan_map[in1], "crd") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "crd")
                else:
                    map_broad[(chan_map[in1], "crd")] = []
                if (chan_map[in2], "ref") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in2], 1, "ref")
                else:
                    map_broad[(chan_map[in2], "ref")] = []
                if (chan_map[in3], "crd") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in3], 1, "crd")
                else:
                    map_broad[(chan_map[in3], "crd")] = []
                if (chan_map[in4], "ref") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in4], 1, "ref")
                else:
                    map_broad[(chan_map[in4], "ref")] = []

                out1 = operator.joiner.output_ref1.id.id
                if out1 not in chan_map and out1 != 0:
                    chan_map[out1] = max_channel_id
                    operator.joiner.output_ref1.id.id = max_channel_id
                    max_channel_id += 1
                elif out1 != 0:
                    operator.joiner.output_ref1.id.id = chan_map[out1]

                out2 = operator.joiner.output_ref2.id.id
                if out2 not in chan_map and out2 != 0:
                    chan_map[out2] = max_channel_id
                    operator.joiner.output_ref2.id.id = max_channel_id
                    max_channel_id += 1
                elif out2 != 0:
                    operator.joiner.output_ref2.id.id = chan_map[out2]

                out3 = operator.joiner.output_crd.id.id
                if out3 not in chan_map and out3 != 0:
                    chan_map[out3] = max_channel_id
                    operator.joiner.output_crd.id.id = max_channel_id
                    max_channel_id += 1
                elif out3 != 0:
                    operator.joiner.output_crd.id.id = chan_map[out3]

                if i not in dependencies:
                    tensor_1 = operator.joiner.input_pairs[0].crd.name[-1]
                    tensor_2 = operator.joiner.input_pairs[1].crd.name[-1]
                    if operator.fiber_lookup.index in shared_vars:
                        out_crd = ""
                        out_ref = ""
                        # out_crd = operator.joiner.input_pairs[0].crd if tensor_1 in shared_tens else
                        if tensor_1 in shared_tens:
                            out_crd = operator.joiner.input_pairs[0].crd.id.id
                            out_ref = operator.joiner.input_pairs[0].ref.id.id
                        elif tensor_2 in shared_tens:
                            out_crd = operator.joiner.input_pairs[1].crd.id.id
                            out_ref = operator.joiner.input_pairs[1].ref.id.id
                        interm_outs[(operator.fiber_lookup.index,
                                     "crd")] = chan_map[out_crd]
                        interm_outs[(operator.fiber_lookup.index,
                                     "ref")] = chan_map[out_ref]

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "crd")].append(
                    new_operator.joiner.input_pairs[0].crd)
                map_broad[(chan_map[in2], "ref")].append(
                    new_operator.joiner.input_pairs[0].ref)
                map_broad[(chan_map[in3], "crd")].append(
                    new_operator.joiner.input_pairs[1].crd)
                map_broad[(chan_map[in4], "ref")].append(
                    new_operator.joiner.input_pairs[1].ref)

            elif op == "repeatsig":
                in1 = operator.repeatsig.input_crd.id.id
                repsig_index = operator.repeatsig.index
                not_in_repsig = False

                # If there's already a repsiggen for same index, reuse it
                if i in dependencies and operator.repeatsig.index in shared_vars:
                    chan_map[in1] = interm_outs[(
                        operator.repeatsig.index, "crd")]
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.repeatsig.input_crd.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.repeatsig.input_crd.id.id = chan_map[in1]
                if (chan_map[in1], "crd") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "crd")
                else:
                    map_broad[(chan_map[in1], "crd")] = []

                new_operator = []
                if repsig_index not in repsiggen:
                    new_program_graph.operators.add().CopyFrom(operator)
                    new_operator = new_program_graph.operators[-1]
                    # repsiggen[repsig_index] = new_operator.repeatsig
                    new_operator.id = max_node_id
                else:
                    new_operator = operator

                map_broad[(chan_map[in1], "crd")].append(
                    new_operator.repeatsig.input_crd)

                out1 = new_operator.repeatsig.output_rep_sig.id.id
                if out1 not in chan_map:
                    chan_map[out1] = max_channel_id
                    new_operator.repeatsig.output_rep_sig.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    new_operator.repeatsig.output_rep_sig.id.id = chan_map[out1]
                if repsig_index not in repsiggen:
                    repsiggen[repsig_index] = new_operator.repeatsig
                    not_in_repsig = True

            elif op == "val_write":
                in1 = operator.val_write.input_val.id.id
                if i not in dependencies:
                    interm_outs[(operator.val_write.tensor, "val")
                                ] = chan_map[operator.val_write.input_val.id.id]
                    continue
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.val_write.input_val.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.val_write.input_val.id.id = chan_map[in1]
                if (chan_map[in1], "val") in map_broad:
                    set_or_create(map_channel_broadcast, in1, 1, "val")
                else:
                    map_broad[(chan_map[in1], "val")] = []

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "val")].append(
                    new_operator.fiber_write.input_crd)
            elif op == "fiber_write":
                in1 = operator.fiber_write.input_crd.id.id
                if i not in dependencies:
                    continue
                fiber_write_index = operator.fiber_write.index
                # if fiber_write_index in repsiggen:
                #     print(repsiggen[fiber_write_index])
                #     in1 = chan_map[repsiggen[fiber_write_index].input_crd.id.id]
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.fiber_write.input_crd.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.fiber_write.input_crd.id.id = chan_map[in1]
                if (chan_map[in1], "crd") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "crd")
                else:
                    map_broad[(chan_map[in1], "crd")] = []

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "crd")].append(
                    new_operator.fiber_write.input_crd)
            elif op == "array":
                in1 = operator.array.input_ref.id.id
                if i in dependencies and operator.array.tensor in shared_tens:
                    tensor_to_chan[operator.array.output_val.id.id] = operator.array.tensor
                    continue
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.array.input_ref.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.array.input_ref.id.id = chan_map[in1]
                if (chan_map[in1], "ref") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "ref")
                else:
                    map_broad[(chan_map[in1], "ref")] = []

                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id

                map_broad[(chan_map[in1], "ref")].append(
                    new_operator.array.input_ref)
                out1 = new_operator.array.output_val.id.id
                if out1 not in chan_map:
                    chan_map[out1] = max_channel_id
                    new_operator.array.output_val.id.id = max_channel_id
                    max_channel_id += 1
                # tensor_to_chan[operator.array.tensor] = operator.array.output_val
            elif op == "alu":
                in1 = operator.alu.vals.inputs[0].id.id
                in2 = operator.alu.vals.inputs[1].id.id

                if in1 in tensor_to_chan:
                    chan_map[in1] = interm_outs[(tensor_to_chan[in1], "val")]
                    print(chan_map[in1])
                elif in2 in tensor_to_chan:
                    chan_map[in2] = interm_outs[(tensor_to_chan[in2], "val")]
                    print(chan_map[in2])

                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.alu.vals.inputs[0].id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.alu.vals.inputs[0].id.id = chan_map[in1]
                if in2 not in chan_map:
                    chan_map[in2] = max_channel_id
                    operator.alu.vals.inputs[1].id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.alu.vals.inputs[1].id.id = chan_map[in2]

                if (chan_map[in1], "val") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "val")
                    # map_channel_broadcast[in1] += 1
                else:
                    map_broad[(chan_map[in1], "val")] = []
                if (chan_map[in2], "val") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in2], 1, "val")
                    # map_channel_broadcast[in2] += 1
                else:
                    map_broad[(chan_map[in2], "val")] = []
                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id
                map_broad[(chan_map[in1], "val")].append(
                    new_operator.alu.vals.inputs[0])
                map_broad[(chan_map[in2], "val")].append(
                    new_operator.alu.vals.inputs[1])
                out1 = new_operator.alu.vals.output.id.id
                if out1 not in chan_map:
                    chan_map[out1] = max_channel_id
                    new_operator.alu.vals.output.id.id = max_channel_id
                    max_channel_id += 1

            elif op == "reduce":
                in1 = operator.reduce.input_val.id.id
                if in1 not in chan_map:
                    chan_map[in1] = max_channel_id
                    operator.reduce.input_val.id.id = max_channel_id
                    max_channel_id += 1
                else:
                    operator.reduce.input_val.id.id = chan_map[in1]
                if (chan_map[in1], "val") in map_broad:
                    set_or_create(map_channel_broadcast,
                                  chan_map[in1], 1, "val")
                else:
                    map_broad[(chan_map[in1], "val")] = []
                new_program_graph.operators.add().CopyFrom(operator)
                new_operator = new_program_graph.operators[-1]
                new_operator.id = max_node_id
                map_broad[(chan_map[in1], "val")].append(
                    new_operator.reduce.input_val)
                out1 = new_operator.reduce.output_val.id.id
                if out1 not in chan_map:
                    chan_map[out1] = max_channel_id
                    new_operator.reduce.output_val.id.id = max_channel_id
                    max_channel_id += 1
            elif op == "coord_drop":
                continue

    # out_comal = "gcn.pbtxt"
    # with open(out_comal, "w") as f:
    #     text_format.PrintMessage(new_program_graph, f)

    input_id_lst = [s[0].id.id for s in map_broad.values()]
    add_void_channels(new_program_graph, input_id_lst)

    insert_broadcast(new_program_graph, map_broad, map_channel_broadcast,
                     max_node_id, max_channel_id)

    # for operator in operators1:
    #     op = operator.WhichOneof("op")
    #     op_id = operator.id
    #     max_node_id = max(max_node_id, op_id)
    #     max_id = process_funcs[op](operator, map_broad, map_channel_broadcast)
    #     max_channel_id = max(max_channel_id, max_id)

    # insert_broadcast(program1, map_broad, map_channel_broadcast,
    #                  max_node_id, max_channel_id)

    comal_graph = comal_pb2.ComalGraph()
    comal_graph.name = "comal graph"
    comal_graph.channel_size = 1024
    comal_graph.graph.CopyFrom(new_program_graph)

    out_comal = "gcn.pbtxt"
    with open(out_comal, "w") as f:
        text_format.PrintMessage(comal_graph, f)

    with open(out_bin, "wb") as f:
        f.write(comal_graph.SerializeToString())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Comal Adapter",
                                     description="Applies optimizations and adds metadata to program graph")
    parser.add_argument('-p', '--proto_file', type=str, nargs='*',
                        help='path of the textproto file')
    parser.add_argument('-o', '--out_bin',
                        help='path of the output comal graph file')
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    if len(args.proto_file) >= 2:
        merge_protos(args.proto_file, args.out_bin)
    else:
        parse_proto(args.proto_file[0], args.out_bin)
        # merge_elementwise(args.proto_file[0], "relu", args.out_bin)
