
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
	type VT = ValType;
	type CT = ValType;
	type ST = ValType;
	let test_name = "test_mult2";
	let filename = home::home_dir().unwrap().join("sam_config.toml");
	let contents = fs::read_to_string(filename).unwrap();
	let data: Data = toml::from_str(&contents).unwrap();
	let formatted_dir = data.sam_config.sam_path;
	let base_path = Path::new(&formatted_dir).join(&test_name);
	let mut parent = Program::default();
	let chan_size = 1024;

	let b0_seg_filename = base_path.join("tensor_B_mode_0_seg");
	let b0_crd_filename = base_path.join("tensor_B_mode_0_crd");
	let b1_seg_filename = base_path.join("tensor_B_mode_1_seg");
	let b1_crd_filename = base_path.join("tensor_B_mode_1_crd");
	let b_vals_filename = base_path.join("tensor_B_mode_vals");

	let b0_seg = read_inputs::<CT>(&b0_seg_filename);
	let b0_crd = read_inputs::<CT>(&b0_crd_filename);
	let b1_seg = read_inputs::<CT>(&b1_seg_filename);
	let b1_crd = read_inputs::<CT>(&b1_crd_filename);
	let b_vals = read_inputs::<VT>(&b_vals_filename);

	let c0_seg_filename = base_path.join("tensor_C_mode_0_seg");
	let c0_crd_filename = base_path.join("tensor_C_mode_0_crd");
	let c1_seg_filename = base_path.join("tensor_C_mode_1_seg");
	let c1_crd_filename = base_path.join("tensor_C_mode_1_crd");
	let c_vals_filename = base_path.join("tensor_C_mode_vals");

	let c0_seg = read_inputs::<CT>(&c0_seg_filename);
	let c0_crd = read_inputs::<CT>(&c0_crd_filename);
	let c1_seg = read_inputs::<CT>(&c1_seg_filename);
	let c1_crd = read_inputs::<CT>(&c1_crd_filename);
	let c_vals = read_inputs::<VT>(&c_vals_filename);

	let (Bi_out_ref_0_sender, Bi_out_ref_0_receiver) = parent.bounded(chan_size);
	let (Bi_out_crd_0_sender, Bi_out_crd_0_receiver) = parent.bounded(chan_size);
	let (Bi_in_ref_0_sender, Bi_in_ref_0_receiver) = parent.bounded(chan_size);
	let gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, "D").into_iter(), Bi_in_ref_0_sender);
	parent.add_child(gen);
	let Bi_data = RdScanData::<CT, ST> {Bi_in_ref_0_receiver, Bi_out_ref_0_receiver, Bi_out_crd_0_receiver};
	let Bi_rdscanner = CompressedCrdRdScan::new(Bi_data, B0_seg.clone(), B0_crd.clone());
	parent.add_child(Bi_rdscanner);

	let (out_broadcast0_sender, out_broadcast_receiver) = parent.bounded(chan_size);
	let (out_broadcast0_sender1, out_broadcast_receiver1) = parent.bounded(chan_size);
	let broadcast0 = BroadcastContext::<CT, ST>(Bi_out_crd_0_receiver);
	broadcast0.attach_target(out_broadcast0_sender);
	broadcast0.attach_target(out_broadcast0_sender1);
	parent.add_child(broadcast);

	let (i_out_repsig_sender, i_out_repsig_receiver) = parent.bounded(chan_size);
	let i_repsig_data = RepSigGenData::<CT, ST> {out_broadcast0_receiver1, i_out_repsig_receiver};
	let i_repsig = RepeatSigGen::new(i_repsig_data);
	parent.add_child(i_repsig);

	let (Ci_out_ref_repeat_sender, Ci_out_ref_repeat_receiver) = parent.bounded(chan_size);
	let (Ci_in_ref_sender, Ci_in_ref_receiver) = parent.bounded(chan_size);
	let gen = GeneratorContext::new(|| token_vec!(VT; ST; 0, "D").into_iter(), Ci_in_ref_sender);
	parent.add_child(gen);
	let Ci_rep_data = RepeatData::<CT, ST> {Ci_in_ref_receiver, i_out_repsig_receiver, Ci_out_ref_repeat_receiver};
	let Ci_repeat = Repeat::new(Ci_rep_data);
	parent.add_child(Ci_repeat);

	let (Cj_out_ref_1_sender, Cj_out_ref_1_receiver) = parent.bounded(chan_size);
	let (Cj_out_crd_1_sender, Cj_out_crd_1_receiver) = parent.bounded(chan_size);
	let Cj_data = RdScanData::<CT, ST> {Ci_out_ref_repeat_receiver, Cj_out_ref_1_receiver, Cj_out_crd_1_receiver};
	let Cj_rdscanner = CompressedCrdRdScan::new(Cj_data, C1_seg.clone(), C1_crd.clone());
	parent.add_child(Cj_rdscanner);

	let (out_broadcast1_sender, out_broadcast_receiver) = parent.bounded(chan_size);
	let (out_broadcast1_sender1, out_broadcast_receiver1) = parent.bounded(chan_size);
	let broadcast1 = BroadcastContext::<CT, ST>(Cj_out_crd_1_receiver);
	broadcast1.attach_target(out_broadcast1_sender);
	broadcast1.attach_target(out_broadcast1_sender1);
	parent.add_child(broadcast);

	let (j_out_repsig_sender, j_out_repsig_receiver) = parent.bounded(chan_size);
	let j_repsig_data = RepSigGenData::<CT, ST> {out_broadcast1_receiver1, j_out_repsig_receiver};
	let j_repsig = RepeatSigGen::new(j_repsig_data);
	parent.add_child(j_repsig);

	let (Bj_out_ref_repeat_sender, Bj_out_ref_repeat_receiver) = parent.bounded(chan_size);
	let Bj_rep_data = RepeatData::<CT, ST> {Bi_out_ref_0_receiver, j_out_repsig_receiver, Bj_out_ref_repeat_receiver};
	let Bj_repeat = Repeat::new(Bj_rep_data);
	parent.add_child(Bj_repeat);

	let (Ck_out_ref_0_sender, Ck_out_ref_0_receiver) = parent.bounded(chan_size);
	let (Ck_out_crd_0_sender, Ck_out_crd_0_receiver) = parent.bounded(chan_size);
	let Ck_data = RdScanData::<CT, ST> {Cj_out_ref_1_receiver, Ck_out_ref_0_receiver, Ck_out_crd_0_receiver};
	let Ck_rdscanner = CompressedCrdRdScan::new(Ck_data, C0_seg.clone(), C0_crd.clone());
	parent.add_child(Ck_rdscanner);

	let (Bk_out_ref_1_sender, Bk_out_ref_1_receiver) = parent.bounded(chan_size);
	let (Bk_out_crd_1_sender, Bk_out_crd_1_receiver) = parent.bounded(chan_size);
	let Bk_data = RdScanData::<CT, ST> {Bj_out_ref_repeat_receiver, Bk_out_ref_1_receiver, Bk_out_crd_1_receiver};
	let Bk_rdscanner = CompressedCrdRdScan::new(Bk_data, B1_seg.clone(), B1_crd.clone());
	parent.add_child(Bk_rdscanner);

	let (intersectk_out_ref1_sender, intersectk_out_ref1_receiver) = parent.bounded(chan_size);
	let (intersectk_out_ref2_sender, intersectk_out_ref2_receiver) = parent.bounded(chan_size);
	let (intersectk_out_crd_sender, intersectk_out_crd_receiver) = parent.bounded(chan_size);
	let intersectk_data = CrdJoinerData::<CT, ST> {Bk_out_crd_1_receiver, Bk_out_ref_1_receiver, Ck_out_crd_0_receiver, Ck_out_ref_0_receiver, intersectk_out_crd_receiver, intersectk_out_ref1_receiver, intersectk_out_ref2_receiver};
	let intersectk_joiner = Intersect::new(intersectk_data);
	parent.add_child(intersectk_joiner);

	let (jk_out_crd_outer_sender, jk_out_crd_outer_receiver) = parent.bounded(chan_size);
	let (jk_out_crd_outer_sender, jk_out_crd_outer_receiver) = parent.bounded(chan_size);
	let jk_crddrop_data = CrdManagerData::<CT, ST> {out_broadcast1_receiver, intersectk_out_crd_receiver, jk_out_crd_outer_receiver};
	let jk_crddrop = CrdDrop::new(jk_crddrop_data);
	parent.add_child(jk_crddrop);

	let (ij_out_crd_outer_sender, ij_out_crd_outer_receiver) = parent.bounded(chan_size);
	let (ij_out_crd_outer_sender, ij_out_crd_outer_receiver) = parent.bounded(chan_size);
	let ij_crddrop_data = CrdManagerData::<CT, ST> {out_broadcast0_receiver, jk_out_crd_outer_receiver, ij_out_crd_outer_receiver};
	let ij_crddrop = CrdDrop::new(ij_crddrop_data);
	parent.add_child(ij_crddrop);

	let (C_out_val_sender, C_out_val_receiver) = parent.bounded(chan_size);
	let array_C_data = ArrayData::<CT, VT, ST> {intersectk_out_ref2_receiver, C_out_val_receiver};
	let array_C = Array::<CT, VT, ST>::new(array_C_data, c_vals.clone());
	parent.add_child(array_C);

	let (B_out_val_sender, B_out_val_receiver) = parent.bounded(chan_size);
	let array_B_data = ArrayData::<CT, VT, ST> {intersectk_out_ref1_receiver, B_out_val_receiver};
	let array_B = Array::<CT, VT, ST>::new(array_B_data, b_vals.clone());
	parent.add_child(array_B);

	let (mul_out_val_sender, mul_out_val_receiver) = parent.bounded(chan_size);
	let mul = make_alu(B_out_val_receiver, C_out_val_receiver, mul_out_val_receiver, ALUMulOp());
	parent.add_child(mul);

}
