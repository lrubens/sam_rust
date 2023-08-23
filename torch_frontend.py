import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.parameter import Parameter
import torch.fx as fx
from torch.fx import Node
import time
from typing import List

# TODO: Figure out how to specify the reorder permutation
# Replace with Anduin's registry based approach where each implementation of a kernel uses different iteration order
op_map = {"Linear": {
    "ijk": "{tensor_a}(i,j) = {tensor_b}(i,k)*{tensor_c}(k,j)+{tensor_d}(i) -f={tensor_a}:ss:0,1 -f={tensor_b}:ss:0,1 -f={tensor_c}:ss:1,0 -f={tensor_d}:s"}}
op_map.update({"matmul": {
              "ijk": "{tensor_a}(i,j) = {tensor_b}(i,k)*{tensor_c}(k,j) -f={tensor_a}:ss:0,1 -f={tensor_b}:ss:0,1 -f={tensor_c}:ss:1,0"}})

supported_funcs = ["relu", "softmax", "exp", "sin", "cos"]


def my_compiler(gm: torch.fx.GraphModule, example_inputs: List[torch.Tensor]):
    print("my_compiler() called with FX graph:")
    gm.graph.print_tabular()
    print(example_inputs[0].name)
    inputs = []
    # TODO: Maybe fuse ops here
    ops_to_compile = []

    for item in gm.graph.nodes:
        if item.op == "placeholder":
            inputs.append(item.target)
        if item.op == "call_function":
            if (item.target == torch.matmul):
                op = "matmul"
                out_name = item.name
                args = item.args
                name_map = dict(tensor_a=out_name,
                                tensor_b=args[0], tensor_c=args[1])
                # TODO: Hardcoded for now
                custard_args = op_map[op]["ijk"].format(**name_map)
                print(custard_args)
        if item.op == "call_module":
            submodule_target = gm.get_submodule(item.target)
            submodule_type = type(submodule_target)
            out_name = item.name
            args = item.args
            if submodule_type == nn.modules.linear.Linear:
                op = "Linear"
                name_map = dict(tensor_a=out_name,
                                tensor_b="W", tensor_c=args[0], tensor_d="bias")
                # TODO: Hardcoded for now
                custard_args = op_map[op]["ijk"].format(**name_map)
                print(custard_args)

    return gm.forward  # return a python callable


class GraphConvolution(nn.Module):
    def __init__(self, in_features, out_features):
        super(GraphConvolution, self).__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x, adjacency):
        out = torch.matmul(adjacency, x)
        out = self.linear(out)
        return out


class CustomGCN(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(CustomGCN, self).__init__()
        self.conv1 = GraphConvolution(in_channels, hidden_channels)
        self.conv2 = GraphConvolution(hidden_channels, out_channels)

    # @torch.compile(backend=my_compiler)
    def forward(self, x, adjacency):
        x = self.conv1(x, adjacency)
        # x = torch.matmul(adjacency, x)
        # x = torch.spmm(self.weight, x)
        # x = x + torch.unsqueeze(self.bias, 1)
        x = F.relu(x)
        x = self.conv2(x, adjacency)
        # x = torch.matmul(adjacency, x)
        # x = torch.spmm(self.weight, x)
        # x = x + torch.unsqueeze(torch.unsqueeze(self.bias, 0), 2)
        return x


# Initialize the custom PyTorch GCN model
in_channels = 10
hidden_channels = 10
out_channels = 10
gcn = CustomGCN(in_channels, hidden_channels, out_channels)
traced = torch.fx.symbolic_trace(gcn)
# print(traced.graph)
# print(model_custom)
# @torch.jit.script


@torch.compile(backend=my_compiler)
def fn(a, b):
    out = gcn.forward(a, b)
    return out


a = torch.randn(10, 10)
b = torch.randn(10, 10)
fn(a, b)
