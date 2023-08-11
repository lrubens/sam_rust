package(default_visibility=["//domain:__subpackages__"])

load("@build_stack_rules_proto//python:python_proto_library.bzl", "python_proto_library")

proto_library(
    name = "comal_proto",
    srcs = ["tortilla/proto/comal.proto", "tortilla/proto/ops.proto", "tortilla/proto/stream.proto", "tortilla/proto/tortilla.proto"],
)

python_proto_library(
    name = "python_comal_proto",
    deps = [":comal_proto"],
)

copy_file(
    name="python_comal_file",
    src="python_comal_proto",
    out="lib/comal_pb2.py",
)

py_library(
    name = "comal",
    srcs = [
        ":python_comal_file",
    ],
    visibility = ["//visibility:public"]
)