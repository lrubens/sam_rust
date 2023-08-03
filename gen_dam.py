import tortilla_pb2
import ops_pb2
import stream_pb2
import re
from google.protobuf import text_format


id_to_node = {}
broadcast_cnt = 0


def print_header(fd, test_name):
    fd.write('''
use std::{fs, path::Path};

use criterion::{criterion_group, criterion_main, BatchSize, BenchmarkId, Criterion};
use dam_rs::templates::sam::stkn_dropper::StknDrop;
use dam_rs::token_vec;

use dam_rs::context::broadcast_context::BroadcastContext;
use dam_rs::context::generator_context::GeneratorContext;

use dam_rs::simulation::Program;
use dam_rs::templates::ops::{ALUDivOp, ALUMulOp, ALUSubOp};
use dam_rs::templates::sam::accumulator::{MaxReduce, Reduce, ReduceData, Spacc1, Spacc1Data};
use dam_rs::templates::sam::alu::{make_alu, make_unary_alu};
use dam_rs::templates::sam::array::{Array, ArrayData};
use dam_rs::templates::sam::crd_manager::{CrdDrop, CrdManagerData};
use dam_rs::templates::sam::joiner::{CrdJoinerData, Intersect};
use dam_rs::templates::sam::primitive::{ALUExpOp, Token};
use dam_rs::templates::sam::rd_scanner::{CompressedCrdRdScan, RdScanData};
use dam_rs::templates::sam::repeat::{RepSigGenData, Repeat, RepeatData, RepeatSigGen};
use dam_rs::templates::sam::scatter_gather::{Gather, Scatter};
use dam_rs::templates::sam::test::config::Data;
use dam_rs::templates::sam::utils::read_inputs;

use dam_rs::templates::sam::wr_scanner::{CompressedWrScan, ValsWrScan};
             ''')
    fd.write("\n")
    fd.write("fn " + test_name + "<ValType, CrdType, StopType>() {\n")
    fd.write("\ttype VT = ValType;\n")
    fd.write("\ttype CT = ValType;\n")
    fd.write("\ttype ST = ValType;\n")
    fd.write("\tlet test_name = " + "\"{}\";\n".format(test_name))
    fd.write("\tlet filename = home::home_dir().unwrap().join(\"sam_config.toml\");\n")
    fd.write("\tlet contents = fs::read_to_string(filename).unwrap();\n")
    fd.write("\tlet data: Data = toml::from_str(&contents).unwrap();\n")
    fd.write("\tlet formatted_dir = data.sam_config.sam_path;\n")
    fd.write("\tlet base_path = Path::new(&formatted_dir).join(&test_name);\n")
    fd.write("\tlet mut parent = Program::default();\n")
    fd.write("\tlet chan_size = 1024;\n")
    fd.write("\n")


def parse_proto(fd, proto_file, data_name):
    program = tortilla_pb2.ProgramGraph()

    with open(proto_file, "rb") as f:
        proto_fd = f.read()
        text_format.Parse(proto_fd, program)
        # print(tortilla)
    program_name = program.name
    operators = program.operators

    mode_formats = {}
    tensors_with_formats = program_name.strip("\"").split(",")
    for i, t in enumerate(tensors_with_formats):
        tensor_name, modes = t.split("=")
        mode_format = re.compile(
            "([a-zA-Z]+)([0-9]+)").match(modes).groups()[1]
        # print(mode_format)
        # num_modes = sum(
        #     list(map(lambda x: 1 if x.isdigit() else 0, set(mode_format))))
        if i != 0:
            mode_formats[tensor_name] = mode_format
            for (mode, format) in enumerate(mode_format):
                fd.write(
                    "\tlet {}{mode}_seg_filename = base_path.join(\"tensor_{}_mode_{mode}_seg\");\n".format(tensor_name.lower(), tensor_name, mode=mode))
                fd.write(
                    "\tlet {}{mode}_crd_filename = base_path.join(\"tensor_{}_mode_{mode}_crd\");\n".format(tensor_name.lower(), tensor_name, mode=mode))

            fd.write(
                "\tlet {}_vals_filename = base_path.join(\"tensor_{}_mode_vals\");\n".format(tensor_name.lower(), tensor_name))
            fd.write("\n")

            for (mode, format) in enumerate(mode_format):
                fd.write(
                    "\tlet {t}{mode}_seg = read_inputs::<CT>(&{t}{mode}_seg_filename);\n".format(t=tensor_name.lower(), mode=mode))
                fd.write(
                    "\tlet {t}{mode}_crd = read_inputs::<CT>(&{t}{mode}_crd_filename);\n".format(t=tensor_name.lower(), mode=mode))
            fd.write(
                "\tlet {t}_vals = read_inputs::<VT>(&{t}_vals_filename);\n".format(t=tensor_name.lower()))
            fd.write("\n")

    print(mode_formats)

    map_outputs = {}
    for operator in reversed(operators):
        op = operator.WhichOneof("op")
        id = operator.id
        id_to_node[id] = operator
        if op == "fiber_lookup":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            # if "crd" not in map_outputs[operator.id]:
            #     map_outputs[operator.id]["crd"] = []
            # map_outputs[operator.id]["crd"].append(
            #     operator.fiber_lookup.output_crd.id.id)
            if "ref" not in map_outputs[operator.id]:
                map_outputs[operator.id]["ref"] = []
            map_outputs[operator.id]["ref"].append(
                operator.fiber_lookup.input_ref.id.id)
        if op == "repeat":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "repsig" not in map_outputs[operator.id]:
                map_outputs[operator.id]["repsig"] = []
            map_outputs[operator.id]["repsig"].append(
                operator.repeat.input_rep_sig.id.id)
            if not operator.repeat.root:
                if "ref" not in map_outputs[operator.id]:
                    map_outputs[operator.id]["ref"] = []
                map_outputs[operator.id]["ref"].append(
                    operator.repeat.input_ref.id.id)
        if op == "repeatsig":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "crd" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd"] = []
            map_outputs[operator.id]["crd"].append(
                operator.repeatsig.input_crd.id.id)
            if not operator.repeat.root:
                if "ref" not in map_outputs[operator.id]:
                    map_outputs[operator.id]["ref"] = []
                map_outputs[operator.id]["ref"].append(
                    operator.repeat.input_ref.id.id)
        elif op == "fiber_write":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "crd" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd"] = []
            map_outputs[operator.id]["crd"].append(
                operator.fiber_write.input_crd.id.id)
        elif op == "array":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "ref" not in map_outputs[operator.id]:
                map_outputs[operator.id]["ref"] = []
            map_outputs[operator.id]["ref"].append(
                operator.array.input_ref.id.id)
        elif op == "joiner":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "ref1" not in map_outputs[operator.id]:
                map_outputs[operator.id]["ref1"] = []
            map_outputs[operator.id]["ref1"].append(
                operator.joiner.input_pairs[0].ref.id.id)
            if "ref2" not in map_outputs[operator.id]:
                map_outputs[operator.id]["ref2"] = []
            map_outputs[operator.id]["ref2"].append(
                operator.joiner.input_pairs[1].ref.id.id)
            if "crd1" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd1"] = []
            map_outputs[operator.id]["crd1"].append(
                operator.joiner.input_pairs[0].crd.id.id)
            if "crd2" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd2"] = []
            map_outputs[operator.id]["crd2"].append(
                operator.joiner.input_pairs[1].crd.id.id)
        elif op == "reduce":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "val" not in map_outputs[operator.id]:
                map_outputs[operator.id]["val"] = []
            map_outputs[operator.id]["val"].append(
                operator.reduce.input_val.id.id)
        elif op == "alu":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "val1" not in map_outputs[operator.id]:
                map_outputs[operator.id]["val1"] = []
            map_outputs[operator.id]["val1"].append(
                operator.alu.vals.inputs[0].id.id)
            if "val2" not in map_outputs[operator.id]:
                map_outputs[operator.id]["val2"] = []
            map_outputs[operator.id]["val2"].append(
                operator.alu.vals.inputs[1].id.id)
        elif op == "coord_drop":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "crd1" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd1"] = []
            map_outputs[operator.id]["crd1"].append(
                operator.coord_drop.input_inner_crd.id.id)
            if "crd2" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd2"] = []
            map_outputs[operator.id]["crd2"].append(
                operator.coord_drop.input_outer_crd.id.id)
        elif op == "coord_hold":
            if operator.id not in map_outputs:
                map_outputs[operator.id] = {}
            if "crd1" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd1"] = []
            map_outputs[operator.id]["crd1"].append(
                operator.coord_hold.input_inner_crd.id.id)
            if "crd2" not in map_outputs[operator.id]:
                map_outputs[operator.id]["crd2"] = []
            map_outputs[operator.id]["crd2"].append(
                operator.coord_hold.input_outer_crd.id.id)

    # for (key, val) in map_outputs.items():

    print(map_outputs)

    map_to_channel = {}

    # std::sort(program.mutable_operators())

    for operator in operators:
        name = operator.name
        id = operator.id
        op = operator.WhichOneof("op")

        if op == "fiber_lookup":
            process_fiberlookup(fd, operator, map_to_channel)
        elif op == "repeat":
            process_repeat(fd, operator, map_to_channel)
        elif op == "joiner":
            process_joiner(fd, operator, map_to_channel)
        elif op == "repeatsig":
            process_rep_sig(fd, operator, map_to_channel)
        elif op == "coord_drop":
            process_crddrop(fd, operator, map_to_channel)
        elif op == "array":
            process_array(fd, operator, map_to_channel)
        elif op == "alu":
            process_alu(fd, operator, map_to_channel)
    fd.write("}\n")


def process_joiner(fd, operator, map_out_channel):
    id = operator.id
    joiner_type = operator.name
    op = operator.joiner

    ref1_id = operator.joiner.output_ref1.id.id
    ref2_id = operator.joiner.output_ref2.id.id
    crd_id = operator.joiner.output_crd.id.id

    fd.write(
        f"\tlet (channel_{ref1_id}_send, channel_{ref1_id}_rcv) = parent.bounded(chan_size);\n")
    fd.write(
        f"\tlet (channel_{ref2_id}_send, channel_{ref2_id}_rcv) = parent.bounded(chan_size);\n")
    fd.write(
        f"\tlet (channel_{crd_id}_send, channel_{crd_id}_rcv) = parent.bounded(chan_size);\n")

    map_out_channel[id] = {"crd": "{t}{i}_out_crd_receiver".format(
        t=joiner_type, i=op.index), "ref1": "{t}{i}_out_ref1_receiver".format(t=joiner_type, i=op.index),
        "ref2": "{t}{i}_out_ref2_receiver".format(t=joiner_type, i=op.index)}

    # print(op.input_pairs[0])

    fd.write("\tlet {t}{i}_data = CrdJoinerData::<CT, ST> ".format(t=joiner_type, i=op.index) + "{" + "{ic1}, {ir1}, {ic2}, {ir2}, {oc}, {or1}, {or2}".format(
        ic1=map_out_channel[op.input_pairs[0].crd.id.id]["crd"], ir1=map_out_channel[op.input_pairs[0].ref.id.id]["ref"],
        ic2=map_out_channel[op.input_pairs[1].crd.id.id]["crd"], ir2=map_out_channel[op.input_pairs[1].ref.id.id]["ref"],
        oc=map_out_channel[id]['crd'], or1=map_out_channel[id]['ref1'], or2=map_out_channel[id]['ref2']) + "};\n")

    fd.write(
        "\tlet {t}{i}_joiner = Intersect::new({t}{i}_data);\n".format(t=joiner_type, i=op.index))
    fd.write("\tparent.add_child({}{}_joiner);\n".format(joiner_type, op.index))

    fd.write("\n")


def process_array(fd, operator, map_out_channel):
    id = operator.id
    op = operator.array

    fd.write(
        f"\tlet ({op.tensor}_out_val_sender, {op.tensor}_out_val_receiver) = parent.bounded(chan_size);\n")

    map_out_channel[id] = {"val": f"{op.tensor}_out_val_receiver"}

    # print(op.input_pairs[0])

    print(id)
    joiner_types = ["intersect", "union"]
    input_ref = "ref"
    if id_to_node[op.input_ref.id.id].name in joiner_types:
        if id_to_node[op.input_ref.id.id].joiner.output_ref1.id.id == id:
            input_ref = "ref1"
        else:
            input_ref = "ref2"
    fd.write(f"\tlet array_{op.tensor}_data = ArrayData::<CT, VT, ST> " + "{" +
             f"{map_out_channel[op.input_ref.id.id][input_ref]}, {map_out_channel[id]['val']}" + "};\n")

    fd.write(
        f"\tlet array_{op.tensor} = Array::<CT, VT, ST>::new(array_{op.tensor}_data, {op.tensor.lower()}_vals.clone());\n")
    fd.write(f"\tparent.add_child(array_{op.tensor});\n")

    fd.write("\n")


def process_fiberlookup(fd, operator, map_out_channel):
    op = operator.fiber_lookup
    id = operator.id
    root = op.root
    print(root)
    fd.write("\tlet ({t}{i}_out_ref_{m}_sender, {t}{i}_out_ref_{m}_receiver) = parent.bounded(chan_size);\n".format(
        t=op.tensor, i=op.index, m=op.mode))
    fd.write("\tlet ({t}{i}_out_crd_{m}_sender, {t}{i}_out_crd_{m}_receiver) = parent.bounded(chan_size);\n".format(
        t=op.tensor, i=op.index, m=op.mode))

    map_out_channel[id] = {"crd": "{t}{i}_out_crd_{m}_receiver".format(
        t=op.tensor, i=op.index, m=op.mode), "ref": "{t}{i}_out_ref_{m}_receiver".format(t=op.tensor, i=op.index, m=op.mode)}

    if root:
        # fd.write("")
        fd.write("\tlet ({t}{i}_in_ref_{m}_sender, {t}{i}_in_ref_{m}_receiver) = parent.bounded(chan_size);\n".format(
            t=op.tensor, i=op.index, m=op.mode))
        fd.write(
            "\tlet gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, \"D\").into_iter(), {}{}_in_ref_{}_sender);\n".format(op.tensor, op.index, op.mode))
        fd.write("\tparent.add_child(gen);\n")
        fd.write("\tlet {t}{i}_data = RdScanData::<CT, ST> ".format(t=op.tensor, i=op.index) + "{" + "{t}{i}_in_ref_{m}_receiver, {r}, {c}".format(
            t=op.tensor, i=op.index, m=op.mode, r=map_out_channel[id]["ref"], c=map_out_channel[id]["crd"]) + "};\n")
    else:
        joiner_types = ["intersect", "union"]
        input_ref = "ref"
        if id_to_node[op.input_ref.id.id].name in joiner_types:
            if id_to_node[op.input_ref.id.id].joiner.output_ref1.id.id == id:
                input_ref = "ref1"
            else:
                input_ref = "ref2"
        fd.write("\tlet {t}{i}_data = RdScanData::<CT, ST> ".format(t=op.tensor, i=op.index) + "{" + "{i}, {r}, {c}".format(
            i=map_out_channel[op.input_ref.id.id][input_ref], r=map_out_channel[id]["ref"], c=map_out_channel[id]["crd"]) + "};\n")
    fd.write(
        "\tlet {t}{i}_rdscanner = CompressedCrdRdScan::new({t}{i}_data, {t}{m}_seg.clone(), {t}{m}_crd.clone());\n".format(t=op.tensor, i=op.index, m=op.mode))
    fd.write("\tparent.add_child({}{}_rdscanner);\n".format(op.tensor, op.index))
    fd.write("\n")


def process_repeat(fd, operator, map_out_channel):
    op = operator.repeat
    root = op.root
    id = operator.id
    fd.write("\tlet ({t}{i}_out_ref_{m}_sender, {t}{i}_out_ref_{m}_receiver) = parent.bounded(chan_size);\n".format(
        t=op.tensor, i=op.index, m=operator.name))

    map_out_channel[id] = {"ref": "{t}{i}_out_ref_{m}_receiver".format(
        t=op.tensor, i=op.index, m=operator.name)}

    if root:
        # fd.write("")
        fd.write("\tlet ({t}{i}_in_ref_sender, {t}{i}_in_ref_receiver) = parent.bounded(chan_size);\n".format(
            t=op.tensor, i=op.index))
        fd.write(
            "\tlet gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, \"D\").into_iter(), {}{}_in_ref_sender);\n".format(op.tensor, op.index))
        fd.write("\tparent.add_child(gen);\n")

        fd.write("\tlet {t}{i}_rep_data = RepeatData::<CT, ST> ".format(t=op.tensor, i=op.index) + "{" + "{t}{i}_in_ref_receiver, {r}, {c}".format(
            t=op.tensor, i=op.index, r=map_out_channel[op.input_rep_sig.id.id]["repsig"], c=map_out_channel[id]["ref"]) + "};\n")
    else:
        joiner_types = ["intersect", "union"]
        input_ref = "ref"
        if id_to_node[op.input_ref.id.id].name in joiner_types:
            if id_to_node[op.input_ref.id.id].joiner.output_ref1.id.id == id:
                input_ref = "ref1"
            else:
                input_ref = "ref2"
        fd.write("\tlet {t}{i}_rep_data = RepeatData::<CT, ST> ".format(t=op.tensor, i=op.index) + "{" + "{i}, {r}, {c}".format(
            i=map_out_channel[op.input_ref.id.id][input_ref], r=map_out_channel[op.input_rep_sig.id.id]["repsig"], c=map_out_channel[id]["ref"]) + "};\n")
    fd.write(
        "\tlet {t}{i}_repeat = Repeat::new({t}{i}_rep_data);\n".format(t=op.tensor, i=op.index))
    fd.write("\tparent.add_child({}{}_repeat);\n".format(op.tensor, op.index))
    fd.write("\n")


def process_broadcast(fd, operator, map_out_channel):
    op = operator.broadcast
    id = operator.id
    global broadcast_cnt
    fd.write(
        f"\tlet (out_broadcast{broadcast_cnt}_sender, out_broadcast_receiver) = parent.bounded(chan_size);\n")
    fd.write(
        f"\tlet (out_broadcast{broadcast_cnt}_sender1, out_broadcast_receiver1) = parent.bounded(chan_size);\n")

    map_out_channel[id] = {
        "crd1": f"out_broadcast{broadcast_cnt}_receiver", "crd2": f"out_broadcast{broadcast_cnt}_receiver1"}

    fd.write(f"\tlet broadcast{broadcast_cnt} = BroadcastContext::<CT, ST>(" + "{i});\n".format(
        i=map_out_channel[op.input.id.id]["crd"]))
    fd.write(
        f"\tbroadcast{broadcast_cnt}.attach_target(out_broadcast{broadcast_cnt}_sender);\n")
    fd.write(
        f"\tbroadcast{broadcast_cnt}.attach_target(out_broadcast{broadcast_cnt}_sender1);\n")
    fd.write("\tparent.add_child(broadcast);\n")
    fd.write("\n")
    broadcast_cnt += 1


def process_rep_sig(fd, operator, map_out_channel):
    op = operator.repeatsig
    id = operator.id
    fd.write("\tlet ({i}_out_repsig_sender, {i}_out_repsig_receiver) = parent.bounded(chan_size);\n".format(
        i=op.index))

    map_out_channel[id] = {"repsig": "{i}_out_repsig_receiver".format(
        i=op.index)}

    input_crd = "crd"
    if id_to_node[op.input_crd.id.id].name == "broadcast":
        if id_to_node[op.input_crd.id.id].broadcast.outputs[0].id.id == id:
            input_crd = "crd1"
        else:
            input_crd = "crd2"

    fd.write("\tlet {i}_repsig_data = RepSigGenData::<CT, ST> ".format(i=op.index) + "{" + "{i}, {r}".format(
        i=map_out_channel[op.input_crd.id.id][input_crd], r=map_out_channel[id]["repsig"]) + "};\n")
    fd.write(
        "\tlet {i}_repsig = RepeatSigGen::new({i}_repsig_data);\n".format(i=op.index))
    fd.write("\tparent.add_child({}_repsig);\n".format(op.index))
    fd.write("\n")


def process_alu(fd, operator, map_out_channel):
    op = operator.alu
    id = operator.id
    name = operator.name
    fd.write(
        f"\tlet ({name}_out_val_sender, {name}_out_val_receiver) = parent.bounded(chan_size);\n")

    map_out_channel[id] = {"val": f"{name}_out_val_receiver"}

    alu_op = ""
    if name == "mul":
        alu_op = "ALUMulOp()"
    elif name == "add":
        alu_op = "ALUAddOp()"
    elif name == "sub":
        alu_op = "ALUSubOp()"

    fd.write(
        f"\tlet {name} = make_alu({map_out_channel[op.vals.inputs[0].id.id]['val']}, {map_out_channel[op.vals.inputs[1].id.id]['val']}, {map_out_channel[id]['val']}, {alu_op});\n")
    fd.write(f"\tparent.add_child({name});\n")
    fd.write("\n")


def process_alu(fd, operator, map_out_channel):
    op = operator.alu
    id = operator.id
    name = operator.name
    fd.write(
        f"\tlet ({name}_out_val_sender, {name}_out_val_receiver) = parent.bounded(chan_size);\n")

    map_out_channel[id] = {"val": f"{name}_out_val_receiver"}

    fd.write(
        f"\tlet {name} = make_alu({map_out_channel[op.vals.inputs[0].id.id]['val']}, {map_out_channel[op.vals.inputs[1].id.id]['val']}, {map_out_channel[id]['val']}, {alu_op});\n")
    fd.write(f"\tparent.add_child({name});\n")
    fd.write("\n")


def process_crddrop(fd, operator, map_out_channel):
    op = operator.coord_drop
    id = operator.id
    fd.write("\tlet ({i}{j}_out_crd_outer_sender, {i}{j}_out_crd_outer_receiver) = parent.bounded(chan_size);\n".format(
        i=op.outer_crd, j=op.inner_crd))
    fd.write("\tlet ({i}{j}_out_crd_outer_sender, {i}{j}_out_crd_outer_receiver) = parent.bounded(chan_size);\n".format(
        i=op.outer_crd, j=op.inner_crd))

    map_out_channel[id] = {"crd": "{i}{j}_out_crd_outer_receiver".format(
        i=op.outer_crd, j=op.inner_crd)}

    print(op.inner_crd)
    print(id)

    input_crd1 = "crd"
    input_crd2 = "crd"
    if id_to_node[op.input_outer_crd.id.id].name == "broadcast":
        prev_op = id_to_node[op.input_outer_crd.id.id]
        if prev_op.broadcast.outputs[0].id.id == id or prev_op.broadcast.outputs[1].id.id == id:
            input_crd1 = "crd1"
        else:
            input_crd1 = "crd2"
    if id_to_node[op.input_inner_crd.id.id].name == "broadcast":
        prev_op = id_to_node[op.input_inner_crd.id.id]
        if prev_op.broadcast.outputs[0].id.id == id or prev_op.broadcast.outputs[1].id.id == id:
            input_crd2 = "crd1"
        else:
            input_crd2 = "crd2"

    print(input_crd1)
    print(input_crd2)

    fd.write(f"\tlet {op.outer_crd}{op.inner_crd}_crddrop_data = CrdManagerData::<CT, ST> " + "{" +
             f"{map_out_channel[op.input_outer_crd.id.id][input_crd1]}, {map_out_channel[op.input_inner_crd.id.id][input_crd2]}, {map_out_channel[id]['crd']}" + "};\n")
    fd.write(
        f"\tlet {op.outer_crd}{op.inner_crd}_crddrop = CrdDrop::new({op.outer_crd}{op.inner_crd}_crddrop_data);\n")
    fd.write(f"\tparent.add_child({op.outer_crd}{op.inner_crd}_crddrop);\n")
    fd.write("\n")


fd = open("generated.rs", "w")
print_header(fd, "test_mult2")
parse_proto(fd, "sam.textproto", "tensor4_mha")

fd.close()
