# GraphSerialize

`graph/util_serialize.py` handles TaskGraph structure serialization and text formatting.

## Main Capabilities

- `build_structure_graph(root_stages, out_edges, stage_runtime_dict)`: Recursively builds a structure JSON from a set of root nodes.
- `format_structure_list_from_graph(root_roots)`: Formats a structure JSON into a printable tree-style text.

## Output Characteristics

- Supports cyclic/reference node marking (`is_ref`).
- Supports multi-root (forest) structure output.
