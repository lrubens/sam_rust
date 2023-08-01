import tortilla_pb2
import ops_pb2
import stream_pb2
import re
from google.protobuf import text_format


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
    fd.write("\ttype VT = ValType\n")
    fd.write("\ttype CT = ValType\n")
    fd.write("\ttype ST = ValType\n")
    fd.write("\tlet test_name = " + "\"{}\"\n".format(test_name))
    fd.write("\tlet filename = home::home_dir().unwrap().join(\"sam_config.toml\");\n")
    fd.write("\tlet contents = fs::read_to_string(filename).unwrap();\n")
    fd.write("\tlet data: Data = toml::from_str(&contents).unwrap();\n")
    fd.write("\tlet formatted_dir = data.sam_config.sam_path;\n")
    fd.write("\tlet base_path = Path::new(&formatted_dir).join(&test_name);\n")


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
            "([a-zA-Z]+)([0-9]+)").match(modes).groups()[0]
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
                "\tlet {t}_vals = read_inputs::<CT>(&{t}_vals_filename);\n".format(t=tensor_name.lower()))
            fd.write("\n")
    fd.write("\tlet mut parent = Program::default();\n")
    fd.write("\tlet chan_size = 1024\n")

    for operator in reversed(operators):
        name = operator.name
        id = operator.id
        op = operator.WhichOneof("op")

        if op == "fiber_lookup":
            new_op = operator.fiber_lookup
            root = new_op.root
            print(root)
            if root:
                print(new_op.label)
                fd.write(
                    "\tlet gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, \"D\").into_iter(), in_ref_sender)\n")
            # if operator.fibe:
            #     print("true")

        # if operator_op == "broadcast":
        #     broadcast_op = operator.broadcast
        #     # print(broadcast_op.output)
        #     input_id = broadcast_op.input.id
        #     # output_id = broadcast_op.output[0].id

        # #     printing broadcast operators
        #     print(f"Operator: {operator_name}")
        #     print(f"ID: {operator_id}")
        #     print(f"Input ID: {input_id}")
        #     print(f"Output ID: {output_id}")
        # elif operator_op == "fiber_lookup":
        #     fiber_op = operator.fiber_lookup
        #     # print(broadcast_op.output)
        # #     input_id = fiber_op.input.id
        #     output_id = fiber_op.input_ref.id

        # #     printing broadcast operators
        #     print(f"Operator: {operator_name}")
        #     print(f"ID: {operator_id}")
        #     print(f"Output ID: {output_id}")
        # # print(operator)
    fd.write("}\n")


fd = open("generated.rs", "w")
print_header(fd, "test_mult2")
parse_proto(fd, "sam.textproto", "tensor4_mha")

fd.close()
