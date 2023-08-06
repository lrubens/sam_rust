# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: comal.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import tortilla_pb2 as tortilla__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='comal.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0b\x63omal.proto\x1a\x0etortilla.proto\"N\n\nComalGraph\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x14\n\x0c\x63hannel_size\x18\x02 \x01(\x04\x12\x1c\n\x05graph\x18\x03 \x01(\x0b\x32\r.ProgramGraphb\x06proto3'
  ,
  dependencies=[tortilla__pb2.DESCRIPTOR,])




_COMALGRAPH = _descriptor.Descriptor(
  name='ComalGraph',
  full_name='ComalGraph',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='ComalGraph.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='channel_size', full_name='ComalGraph.channel_size', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='graph', full_name='ComalGraph.graph', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=31,
  serialized_end=109,
)

_COMALGRAPH.fields_by_name['graph'].message_type = tortilla__pb2._PROGRAMGRAPH
DESCRIPTOR.message_types_by_name['ComalGraph'] = _COMALGRAPH
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ComalGraph = _reflection.GeneratedProtocolMessageType('ComalGraph', (_message.Message,), {
  'DESCRIPTOR' : _COMALGRAPH,
  '__module__' : 'comal_pb2'
  # @@protoc_insertion_point(class_scope:ComalGraph)
  })
_sym_db.RegisterMessage(ComalGraph)


# @@protoc_insertion_point(module_scope)