import networkx as nx
try:
    import pygraphviz as pgv # pygraphviz installation can be tricky. See docstring.
except ImportError:
    pgv = None # Will be checked in generate_mindmap
    print("Warning: pygraphviz could not be imported. Mind map generation will fail if attempted.")

import uuid # For unique node IDs
import json # For printing structures in main

# Attempt to import from text_processor, assuming it's in the same directory or PYTHONPATH
try:
    from text_processor import process_text_to_structure
except ImportError:
    process_text_to_structure = None
    print("Warning: text_processor.py not found or process_text_to_structure could not be imported. The __main__ example will use dummy data or fail if it relies on it.")


def _build_graph_recursive(data_structure: list, graph: nx.DiGraph, parent_node_id=None, node_id_map=None):
    """
    Recursively builds a NetworkX DiGraph from the hierarchical data structure.

    Args:
        data_structure: The list of dictionaries representing the hierarchy.
        graph: The NetworkX DiGraph object to populate.
        parent_node_id: The ID of the parent node in the graph for the current level of recursion.
        node_id_map: A dictionary to map text content to unique node IDs to handle non-unique text.
    """
    if node_id_map is None:
        node_id_map = {}

    for item in data_structure:
        node_text = item.get("text", "Untitled") # Default text if missing
        
        current_node_id = str(uuid.uuid4().hex[:12]) 

        graph.add_node(current_node_id, label=node_text)

        if parent_node_id:
            graph.add_edge(parent_node_id, current_node_id)

        children = item.get("children", [])
        if children:
            _build_graph_recursive(children, graph, current_node_id, node_id_map)

def generate_mindmap(data_structure: list, output_filename: str, style_attributes: dict = None):
    """
    Generates a mind map image from a hierarchical data structure.
    (Function body remains the same, error checking for pgv will be important)
    """
    if pgv is None:
        print("Error: pygraphviz is not installed or could not be imported. Cannot generate mind map.")
        return

    if not data_structure:
        print("Input data structure is empty. Cannot generate mind map.")
        return

    nx_graph = nx.DiGraph()
    _build_graph_recursive(data_structure, nx_graph)

    if not nx_graph.nodes():
        print("No nodes were added to the graph (data_structure might be malformed or empty). Cannot generate mind map.")
        return

    try:
        agraph = nx.nx_agraph.to_agraph(nx_graph)
    except Exception as e:
        print(f"Error converting NetworkX graph to AGraph: {e}")
        print("This can happen if pygraphviz is not correctly installed or if there's an issue with node IDs.")
        # Fallback attempt for environments where to_agraph might require explicit string conversion again
        # (though _build_graph_recursive should ensure string IDs via UUIDs)
        try:
            print("Retrying graph conversion with explicit string node mapping...")
            mapping = {node: str(node) for node in nx_graph.nodes()}
            nx_graph_str_nodes = nx.relabel_nodes(nx_graph, mapping, copy=True)
            agraph = nx.nx_agraph.to_agraph(nx_graph_str_nodes)
            print("Graph conversion retry successful.")
        except Exception as e_relabel:
            print(f"Error converting NetworkX graph to AGraph even after relabeling: {e_relabel}")
            return
    
    default_styles = {
        'graph': {
            'rankdir': 'TB', 'splines': 'ortho', 'nodesep': '0.4', 'ranksep': '0.8', 
            'bgcolor': 'transparent', 'fontname': 'Helvetica', 'concentrate': 'true',
        },
        'node': {
            'shape': 'box', 'style': 'filled,rounded', 'fillcolor': '#ADD8E6', 
            'fontname': 'Helvetica', 'fontsize': '10', 'margin': '0.15,0.05',
        },
        'edge': {
            'color': '#808080', 'arrowsize': '0.7', 'penwidth': '1.0', 'fontname': 'Helvetica',
        }
    }

    if style_attributes:
        for element_type in ['graph', 'node', 'edge']:
            if element_type in style_attributes:
                default_styles[element_type].update(style_attributes[element_type])

    agraph.graph_attr.update(default_styles['graph'])
    agraph.node_attr.update(default_styles['node'])
    agraph.edge_attr.update(default_styles['edge'])
    
    for n_id, n_attrs in nx_graph.nodes(data=True):
        try:
            agraph_node = agraph.get_node(str(n_id)) # Ensure node ID is string for AGraph
            agraph_node.attr['label'] = n_attrs.get('label', str(n_id))
        except KeyError: # pragma: no cover (defensive)
            print(f"Warning: Node ID {n_id} from NetworkX graph not found in AGraph. Skipping label set.")

    try:
        agraph.draw(output_filename, prog='dot')
        print(f"Mind map generated successfully: {output_filename}")
    except Exception as e: # pragma: no cover (hard to test without real pygraphviz)
        print(f"Error rendering graph with PyGraphviz/Graphviz: {e}")
        print(f"Ensure Graphviz is installed and the 'dot' command is in your system's PATH.")
        print(f"Attempted to create: {output_filename}")


if __name__ == '__main__': # pragma: no cover
    print("Running mindmap_generator.py example...")
    # ... (rest of __main__ remains the same) ...
    if pgv is None:
        print("PyGraphviz not available, cannot run __main__ generation examples.")
    elif process_text_to_structure is None:
        print("Using dummy data structure for mindmap generation as text_processor.py or its function could not be imported.")
        sample_data_structure = [
            {"text": "Central Topic", "children": [
                {"text": "Branch 1", "children": [
                    {"text": "Sub-Branch 1.1", "children": []},
                    {"text": "Sub-Branch 1.2", "children": []}
                ]},
                {"text": "Branch 2", "children": [
                    {"text": "Sub-Branch 2.1", "children": []}
                ]},
                {"text": "Branch 3", "children": []}
            ]}
        ]
        print("\nGenerated data structure for mind map:")
        print(json.dumps(sample_data_structure, indent=2))
        output_file_default = "sample_mindmap_default.png"
        print(f"\nGenerating mind map with default style: {output_file_default}")
        generate_mindmap(sample_data_structure, output_file_default)
    else:
        sample_text = (
            "Artificial intelligence is transforming industries. "
            "Machine learning, a subset of AI, enables systems to learn from data. "
            "Deep learning, a part of machine learning, uses neural networks with many layers. "
            "Natural Language Processing allows computers to understand human language."
        )
        print(f"\nProcessing sample text: \"{sample_text}\"")
        sample_data_structure = process_text_to_structure(sample_text)

        if not sample_data_structure:
            print("Sample data structure is empty (either from text_processor or dummy). Exiting example.")
        else:
            print("\nGenerated data structure for mind map:")
            print(json.dumps(sample_data_structure, indent=2))

            output_file_default = "sample_mindmap_default.png"
            print(f"\nGenerating mind map with default style: {output_file_default}")
            generate_mindmap(sample_data_structure, output_file_default)

            custom_styles = {
                'graph': {
                    'rankdir': 'LR', 'bgcolor': '#f4f4f4', 'nodesep': '0.5', 'ranksep': '1.2',
                },
                'node': {
                    'shape': 'ellipse', 'style': 'filled', 'fillcolor': '#90EE90', 
                    'fontname': 'Arial', 'fontsize': '11', 'fontcolor': '#333333',
                },
                'edge': {
                    'color': '#4682B4', 'style': 'solid', 'arrowsize': '0.6', 'penwidth': '1.2',
                }
            }
            output_file_custom = "sample_mindmap_custom.png"
            print(f"\nGenerating mind map with custom style: {output_file_custom}")
            generate_mindmap(sample_data_structure, output_file_custom, style_attributes=custom_styles)

            print("\nTesting generation with empty data structure (should print an error message):")
            generate_mindmap([], "empty_mindmap.png")

            if process_text_to_structure:
                complex_text = "Project management involves planning, execution, and monitoring. Key areas include scope, time, and budget management. Risk assessment is also crucial."
                print(f"\nProcessing complex text: \"{complex_text}\"")
                complex_data = process_text_to_structure(complex_text)
                print("\nGenerated data structure for complex text:")
                print(json.dumps(complex_data, indent=2))
                if complex_data:
                     generate_mindmap(complex_data, "complex_mindmap.png")

    print("\nMindmap generator example finished.")
