
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
             
fn test_mult2<ValType, CrdType, StopType>() {
	type VT = ValType
	type CT = ValType
	type ST = ValType
	let test_name = "test_mult2"
	let filename = home::home_dir().unwrap().join("sam_config.toml");
	let contents = fs::read_to_string(filename).unwrap();
	let data: Data = toml::from_str(&contents).unwrap();
	let formatted_dir = data.sam_config.sam_path;
	let base_path = Path::new(&formatted_dir).join(&test_name);
	let q0_seg_filename = base_path.join("tensor_Q_mode_0_seg");
	let q0_crd_filename = base_path.join("tensor_Q_mode_0_crd");
	let q1_seg_filename = base_path.join("tensor_Q_mode_1_seg");
	let q1_crd_filename = base_path.join("tensor_Q_mode_1_crd");
	let q2_seg_filename = base_path.join("tensor_Q_mode_2_seg");
	let q2_crd_filename = base_path.join("tensor_Q_mode_2_crd");
	let q3_seg_filename = base_path.join("tensor_Q_mode_3_seg");
	let q3_crd_filename = base_path.join("tensor_Q_mode_3_crd");
	let q_vals_filename = base_path.join("tensor_Q_mode_vals");

	let q0_seg = read_inputs::<CT>(&q0_seg_filename);
	let q0_crd = read_inputs::<CT>(&q0_crd_filename);
	let q1_seg = read_inputs::<CT>(&q1_seg_filename);
	let q1_crd = read_inputs::<CT>(&q1_crd_filename);
	let q2_seg = read_inputs::<CT>(&q2_seg_filename);
	let q2_crd = read_inputs::<CT>(&q2_crd_filename);
	let q3_seg = read_inputs::<CT>(&q3_seg_filename);
	let q3_crd = read_inputs::<CT>(&q3_crd_filename);
	let q_vals = read_inputs::<CT>(&q_vals_filename);

	let k0_seg_filename = base_path.join("tensor_K_mode_0_seg");
	let k0_crd_filename = base_path.join("tensor_K_mode_0_crd");
	let k1_seg_filename = base_path.join("tensor_K_mode_1_seg");
	let k1_crd_filename = base_path.join("tensor_K_mode_1_crd");
	let k2_seg_filename = base_path.join("tensor_K_mode_2_seg");
	let k2_crd_filename = base_path.join("tensor_K_mode_2_crd");
	let k3_seg_filename = base_path.join("tensor_K_mode_3_seg");
	let k3_crd_filename = base_path.join("tensor_K_mode_3_crd");
	let k_vals_filename = base_path.join("tensor_K_mode_vals");

	let k0_seg = read_inputs::<CT>(&k0_seg_filename);
	let k0_crd = read_inputs::<CT>(&k0_crd_filename);
	let k1_seg = read_inputs::<CT>(&k1_seg_filename);
	let k1_crd = read_inputs::<CT>(&k1_crd_filename);
	let k2_seg = read_inputs::<CT>(&k2_seg_filename);
	let k2_crd = read_inputs::<CT>(&k2_crd_filename);
	let k3_seg = read_inputs::<CT>(&k3_seg_filename);
	let k3_crd = read_inputs::<CT>(&k3_crd_filename);
	let k_vals = read_inputs::<CT>(&k_vals_filename);

	let mut parent = Program::default();
	let chan_size = 24
	let gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, "D").into_iter(), in_ref_sender)
	let gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, "D").into_iter(), in_ref_sender)
}
