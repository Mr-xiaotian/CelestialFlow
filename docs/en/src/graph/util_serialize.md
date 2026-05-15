# GraphSerialize

> 📅 Last Updated: 2026/05/15

`graph/util_serialize.py` handles TaskGraph structure serialization and text formatting.

## Main Capabilities

- `build_structure_graph(source_stages, out_edges, stage_runtime_dict)`: Recursively builds a structure JSON from a set of source nodes.
- `format_structure_list_from_graph(roots)`: Formats the structure JSON into a printable tree-style text.

## Output Characteristics

- Supports cyclic/reference node marking (`is_ref`).
- Supports multi-source node (forest) structure output.
