# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: stream.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cstream.proto\x12\x08tortilla\"[\n\tRefStream\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.tortilla.RefStream.StreamID\x12\x0c\n\x04name\x18\x02 \x01(\t\x1a\x16\n\x08StreamID\x12\n\n\x02id\x18\x01 \x01(\x04\"[\n\tValStream\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.tortilla.ValStream.StreamID\x12\x0c\n\x04name\x18\x02 \x01(\t\x1a\x16\n\x08StreamID\x12\n\n\x02id\x18\x01 \x01(\x04\"[\n\tCrdStream\x12(\n\x02id\x18\x01 \x01(\x0b\x32\x1c.tortilla.CrdStream.StreamID\x12\x0c\n\x04name\x18\x02 \x01(\t\x1a\x16\n\x08StreamID\x12\n\n\x02id\x18\x01 \x01(\x04\"a\n\x0cRepSigStream\x12+\n\x02id\x18\x01 \x01(\x0b\x32\x1f.tortilla.RepSigStream.StreamID\x12\x0c\n\x04name\x18\x02 \x01(\t\x1a\x16\n\x08StreamID\x12\n\n\x02id\x18\x01 \x01(\x04\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'stream_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_REFSTREAM']._serialized_start=26
  _globals['_REFSTREAM']._serialized_end=117
  _globals['_REFSTREAM_STREAMID']._serialized_start=95
  _globals['_REFSTREAM_STREAMID']._serialized_end=117
  _globals['_VALSTREAM']._serialized_start=119
  _globals['_VALSTREAM']._serialized_end=210
  _globals['_VALSTREAM_STREAMID']._serialized_start=95
  _globals['_VALSTREAM_STREAMID']._serialized_end=117
  _globals['_CRDSTREAM']._serialized_start=212
  _globals['_CRDSTREAM']._serialized_end=303
  _globals['_CRDSTREAM_STREAMID']._serialized_start=95
  _globals['_CRDSTREAM_STREAMID']._serialized_end=117
  _globals['_REPSIGSTREAM']._serialized_start=305
  _globals['_REPSIGSTREAM']._serialized_end=402
  _globals['_REPSIGSTREAM_STREAMID']._serialized_start=95
  _globals['_REPSIGSTREAM_STREAMID']._serialized_end=117
# @@protoc_insertion_point(module_scope)
