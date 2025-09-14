from typing import BinaryIO
import json

from atmst.mst.node import MSTNode
from atmst.mst.node_store import NodeStore
from atmst.mst.node_wrangler import NodeWrangler
from atmst.mst.node_walker import NodeWalker
from atmst.mst.diff import very_slow_mst_diff, record_diff
from atmst.blockstore import MemoryBlockStore
from atmst.blockstore.car_file import encode_varint
import cbrrr
from cbrrr import CID

class CarWriter:
	def __init__(self, stream: BinaryIO, root: cbrrr.CID) -> None:
		self.stream = stream
		header_bytes = cbrrr.encode_dag_cbor(
			{"version": 1, "roots": [root]}
		)
		stream.write(encode_varint(len(header_bytes)))
		stream.write(header_bytes)

	def write_block(self, cid: cbrrr.CID, value: bytes):
		cid_bytes = bytes(cid)
		self.stream.write(encode_varint(len(cid_bytes) + len(value)))
		self.stream.write(cid_bytes)
		self.stream.write(value)

keys = []
key_heights = [0, 1, 0, 2, 0, 1, 0] # if all these keys are added to a MST, it'll form a perfect binary tree.
i = 0
for height in key_heights:
	while True:
		key = f"k/{i:02d}"
		i += 1
		if MSTNode.key_height(key) == height:
			keys.append(key)
			break

vals = [CID.cidv1_dag_cbor_sha256_32_from(cbrrr.encode_dag_cbor({"$type": "mst-test-data", "value_for": k})) for k in keys]

print(keys)
print(vals)

# we can reuse these
bs = MemoryBlockStore()
ns = NodeStore(bs)
wrangler = NodeWrangler(ns)

roots = []

for i in range(2**len(keys)):
	filename = f"./cars/exhaustive/exhaustive_{i:03d}.car"
	root = ns.get_node(None).cid
	for j in range(len(keys)):
		if (i>>j) & 1:
			#filename += f"_{keys[j]}h{key_heights[j]}"
			root = wrangler.put_record(root, keys[j], vals[j])
	#filename += ".car"
	print(i, filename)

	car_blocks = []
	for node in NodeWalker(ns, root).iter_nodes():
		car_blocks.append((node.cid, node.serialised))

	assert(len(set(cid for cid, val in car_blocks)) == len(car_blocks)) # no dupes

	with open(filename, "wb") as carfile:
		car = CarWriter(carfile, root)
		for cid, val in sorted(car_blocks, key=lambda x: bytes(x[0])):
			car.write_block(cid, val)

	roots.append(root)

# generate exhaustive test cases
for ai, root_a in enumerate(roots):
	for bi, root_b in enumerate(roots):
		filename = f"./tests/diff/exhaustive/exhaustive_{ai:03d}_{bi:03d}.json"
		print(filename)
		car_a = f"./cars/exhaustive/exhaustive_{ai:03d}.car"
		car_b = f"./cars/exhaustive/exhaustive_{bi:03d}.car"
		created_nodes, deleted_nodes = very_slow_mst_diff(ns, root_a, root_b)
		record_ops = []
		for delta in record_diff(ns, created_nodes, deleted_nodes):
			record_ops.append({
				"rpath": delta.path,
				"old_value": None if delta.prior_value is None else delta.prior_value.encode(),
				"new_value": None if delta.later_value is None else delta.later_value.encode()
			})
		testcase = {
			"$type": "mst-diff",
			"description": f'procedurally generated MST diff test case between MST {ai} and {bi}',
			"inputs": {
				"mst_a": car_a,
				"mst_b": car_b
			},
			"results": {
				"created_nodes": sorted([cid.encode() for cid in created_nodes]),
				"deleted_nodes": sorted([cid.encode() for cid in deleted_nodes]),
				"record_ops": sorted(record_ops, key=lambda x: x["rpath"]),
				"proof_nodes": "TODO",
				"firehose_cids": "TODO"
			}
		}
		with open(filename, "w") as jsonfile:
			json.dump(testcase, jsonfile, indent="\t")
