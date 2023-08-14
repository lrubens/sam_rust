.PHONY: all clean

all: proto_comal

clean:
	# rm -rf lib/
	rm -rf *_pb2.py

proto_comal: tortilla/proto/*.proto
	# mkdir lib
	protoc -Itortilla/proto --python_out=. tortilla/proto/*.proto