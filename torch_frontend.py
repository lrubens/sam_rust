import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.parameter import Parameter
import time
from typing import List


def my_compiler(gm: torch.fx.GraphModule, example_inputs: List[torch.Tensor]):
    print("my_compiler() called with FX graph:")
    gm.graph.print_tabular()
    # print(gm.graph)
    for item in gm.graph.nodes:
        if item.op == "call_function":
            print("NEW: ", item, item.args, item.name)
    print(gm.forward)
    return gm.forward  # return a python callable


class GraphConvolution(nn.Module):
    def __init__(self, in_features, out_features):
        super(GraphConvolution, self).__init__()
        self.linear = nn.Linear(in_features, out_features)

    # @torch.compile(backend=my_compiler)
    def forward(self, x, adjacency):
        out = torch.matmul(adjacency, x)
        out = self.linear(out)
        return out


class CustomGCN(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(CustomGCN, self).__init__()
        self.conv1 = GraphConvolution(in_channels, hidden_channels)
        self.conv2 = GraphConvolution(hidden_channels, out_channels)
        self.weight = Parameter(torch.FloatTensor(in_channels, out_channels))
        self.bias = Parameter(torch.FloatTensor(out_channels))

    # @torch.compile(backend=my_compiler)
    def forward(self, x, adjacency):
        # x = self.conv1(x, adjacency)
        x = torch.matmul(adjacency, x)
        x = torch.spmm(self.weight, x)
        x = x + torch.unsqueeze(self.bias, 1)
        x = F.relu(x)
        # x = self.conv2(x, adjacency)
        x = torch.matmul(adjacency, x)
        x = torch.spmm(self.weight, x)
        x = x + torch.unsqueeze(torch.unsqueeze(self.bias, 0), 2)
        return x


# Initialize the custom PyTorch GCN model
in_channels = 10
hidden_channels = 10
out_channels = 10
model_custom = CustomGCN(in_channels, hidden_channels, out_channels)
traced = torch.fx.symbolic_trace(model_custom)
# print(traced.graph)
# print(model_custom)
# @torch.jit.script


@torch.compile(backend=my_compiler)
def fn(x, y):
    # a = torch.cos(x)
    # b = torch.sin(y)
    # c = torch.einsum("ik,kj->ij", a, b)
    # d = torch.softmax(c, -1)
    # e = torch.relu(d)
    out = model_custom.forward(x, y)
    return out


fn(torch.randn(10, 10), torch.randn(10, 10))
