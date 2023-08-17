def set_or_create(map, key, val, valtype):
    if key not in map:
        map[key] = (val, valtype)
        return
    map[key] = (map[key][0] + 1, valtype)
    return


def process_fiber_lookup(operator, map_broad, map_channel_broadcast):
    op = operator.WhichOneof("op")
    if op == "fiber_lookup":
        in1 = operator.fiber_lookup.input_ref.id.id
        if (in1, "ref") in map_broad:
            set_or_create(map_channel_broadcast, in1, 1, "ref")
        else:
            map_broad[(in1, "ref")] = []

        map_broad[(in1, "ref")].append(operator.fiber_lookup.input_ref)

    return in1


def process_repeat(operator, map_broad, map_channel_broadcast):
    in1 = operator.repeat.input_rep_sig.id.id
    in2 = operator.repeat.input_ref.id.id
    if (in1, "repsig") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "repsig")
    else:
        map_broad[(in1, "repsig")] = []
    if (in2, "ref") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "ref")
    else:
        map_broad[(in2, "ref")] = []
    map_broad[(in1, "repsig")].append(operator.repeat.input_rep_sig)
    map_broad[(in2, "ref")].append(operator.repeat.input_ref)

    return max(in1, in2)


def process_repeat_sig(operator, map_broad, map_channel_broadcast):
    in1 = operator.repeatsig.input_crd.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
    else:
        map_broad[(in1, "crd")] = []
    map_broad[(in1, "crd")].append(operator.repeatsig.input_crd)
    return in1


def process_fiber_write(operator, map_broad, map_channel_broadcast):
    in1 = operator.fiber_write.input_crd.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
    else:
        map_broad[(in1, "crd")] = []
    map_broad[(in1, "crd")].append(operator.fiber_write.input_crd)
    return in1


def process_val_write(operator, map_broad, map_channel_broadcast):
    in1 = operator.val_write.input_val.id.id
    if (in1, "val") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "val")
    else:
        map_broad[(in1, "val")] = []
    map_broad[(in1, "val")].append(operator.fiber_write.input_crd)
    return in1


def process_array(operator, map_broad, map_channel_broadcast):
    in1 = operator.array.input_ref.id.id
    if (in1, "ref") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "ref")
    else:
        map_broad[(in1, "ref")] = []
    map_broad[(in1, "ref")].append(operator.array.input_ref)
    return in1


def process_joiner(operator, map_broad, map_channel_broadcast):
    in1 = operator.joiner.input_pairs[0].crd.id.id
    in2 = operator.joiner.input_pairs[0].ref.id.id
    in3 = operator.joiner.input_pairs[1].crd.id.id
    in4 = operator.joiner.input_pairs[1].ref.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
    else:
        map_broad[(in1, "crd")] = []
    if (in2, "ref") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "ref")
    else:
        map_broad[(in2, "ref")] = []
    if (in3, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in3, 1, "crd")
    else:
        map_broad[(in3, "crd")] = []
    if (in4, "ref") in map_broad:
        set_or_create(map_channel_broadcast, in4, 1, "ref")
    else:
        map_broad[(in4, "ref")] = []

    map_broad[(in1, "crd")].append(operator.joiner.input_pairs[0].crd)
    map_broad[(in2, "ref")].append(operator.joiner.input_pairs[0].ref)
    map_broad[(in3, "crd")].append(operator.joiner.input_pairs[1].crd)
    map_broad[(in4, "ref")].append(operator.joiner.input_pairs[1].ref)
    return max(in1, in2, in3, in4)


def process_reduce(operator, map_broad, map_channel_broadcast):
    in1 = operator.reduce.input_val.id.id
    if (in1, "val") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "val")
    else:
        map_broad[(in1, "val")] = []
    map_broad[(in1, "val")].append(operator.reduce.input_val)
    # max_channel_id = max(max_channel_id, in1)
    return in1


def process_alu(operator, map_broad, map_channel_broadcast):
    in1 = operator.alu.vals.inputs[0].id.id
    in2 = operator.alu.vals.inputs[1].id.id
    if (in1, "val") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "val")
        # map_channel_broadcast[in1] += 1
    else:
        map_broad[(in1, "val")] = []
    if (in2, "val") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "val")
        # map_channel_broadcast[in2] += 1
    else:
        map_broad[(in2, "val")] = []
    map_broad[(in1, "val")].append(operator.alu.vals.inputs[0])
    map_broad[(in2, "val")].append(operator.alu.vals.inputs[1])
    return max(in1, in2)


def process_coord_drop(operator, map_broad, map_channel_broadcast):
    in1 = operator.coord_drop.input_inner_crd.id.id
    in2 = operator.coord_drop.input_outer_crd.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
    else:
        map_broad[(in1, "crd")] = []
    if (in2, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "crd")
    else:
        map_broad[(in2, "crd")] = []
    map_broad[(in1, "crd")].append(operator.coord_drop.input_inner_crd)
    map_broad[(in2, "crd")].append(operator.coord_drop.input_outer_crd)
    return max(in1, in2)


def process_coord_hold(operator, map_broad, map_channel_broadcast):
    in1 = operator.coord_hold.input_inner_crd.id.id
    in2 = operator.coord_hold.input_outer_crd.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
        # map_channel_broadcast[in1] += 1
    else:
        map_broad[(in1, "crd")] = []
    if (in2, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "crd")
    else:
        map_broad[(in2, "crd")] = []
    map_broad[(in1, "crd")].append(operator.coord_hold.input_inner_crd)
    map_broad[(in2, "crd")].append(operator.coord_hold.input_outer_crd)
    return max(in1, in2)


def process_spacc(operator, map_broad, map_channel_broadcast):
    in1 = operator.spacc.input_inner_crd.id.id
    in2 = operator.spacc.input_outer_crd.id.id
    in3 = operator.spacc.input_val.id.id
    if (in1, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in1, 1, "crd")
        # map_channel_broadcast[in1] += 1
    if (in2, "crd") in map_broad:
        set_or_create(map_channel_broadcast, in2, 1, "crd")
        # map_channel_broadcast[in2] += 1
    else:
        map_broad[(in2, "crd")] = []
    if (in3, "val") in map_broad:
        set_or_create(map_channel_broadcast, in3, 1)
        # map_channel_broadcast[in3] += 1
    else:
        map_broad[(in3, "val")] = []
    map_broad[(in1, "crd")].append(operator.spacc.input_inner_crd)
    map_broad[(in2, "crd")].append(operator.spacc.input_outer_crd)
    map_broad[(in3, "val")].append(operator.spacc.input_val)
    return max(in1, in2, in3)


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


def register_process_funcs(process_ops):
    process_ops["fiber_lookup"] = process_fiber_lookup
    process_ops["repeat"] = process_repeat
    process_ops["repeatsig"] = process_repeat_sig
    process_ops["fiber_write"] = process_fiber_write
    process_ops["val_write"] = process_val_write
    process_ops["array"] = process_array
    process_ops["joiner"] = process_joiner
    process_ops["reduce"] = process_reduce
    process_ops["alu"] = process_alu
    process_ops["coord_drop"] = process_coord_drop
    process_ops["coord_hold"] = process_coord_hold
    process_ops["spacc"] = process_spacc
