import unittest
from unittest.mock import patch, MagicMock, ANY
import networkx as nx

# Import the module to be tested
# mindmap_generator.py now has a try-except for pygraphviz import,
# so it should be importable even if pygraphviz is not working.
from mindmap_generator import generate_mindmap, _build_graph_recursive

# Helper to create a mock AGraph instance with a working `get_node`
def create_mock_agraph():
    mock_agraph = MagicMock(name="AGraphInstance")
    
    # Collection to store mock node objects created by get_node
    mock_nodes_store = {}

    def mock_get_node(node_id):
        node_id_str = str(node_id) # Ensure consistency
        if node_id_str not in mock_nodes_store:
            # Create a new mock for the node if it doesn't exist
            mock_node = MagicMock(name=f"AGraphNode_{node_id_str}")
            mock_node.attr = {} # Each node mock needs its own attr dictionary
            mock_nodes_store[node_id_str] = mock_node
        return mock_nodes_store[node_id_str]

    mock_agraph.get_node.side_effect = mock_get_node
    return mock_agraph


@patch('mindmap_generator.pgv', create=True) # Mocks the 'pgv' module object in mindmap_generator
@patch('mindmap_generator.nx.nx_agraph.to_agraph') # Mocks the to_agraph function
class TestMindmapGenerator(unittest.TestCase):

    def test_build_graph_recursive_simple(self, mock_to_agraph, mock_pgv_module):
        """Test the internal _build_graph_recursive function for basic structure."""
        data = [{"text": "Root", "children": [{"text": "Child1", "children": []}]}]
        graph = nx.DiGraph()
        _build_graph_recursive(data, graph)

        self.assertEqual(graph.number_of_nodes(), 2)
        self.assertEqual(graph.number_of_edges(), 1)

        root_node_id = None
        child1_node_id = None
        for node, attrs in graph.nodes(data=True):
            if attrs.get('label') == "Root":
                root_node_id = node
            elif attrs.get('label') == "Child1":
                child1_node_id = node
        
        self.assertIsNotNone(root_node_id, "Root node not found by label.")
        self.assertIsNotNone(child1_node_id, "Child1 node not found by label.")
        self.assertTrue(graph.has_edge(root_node_id, child1_node_id), "Edge from Root to Child1 not found.")

    def test_build_graph_recursive_empty_data(self, mock_to_agraph, mock_pgv_module):
        """Test _build_graph_recursive with empty data."""
        graph = nx.DiGraph()
        _build_graph_recursive([], graph)
        self.assertEqual(graph.number_of_nodes(), 0)

    def test_generate_mindmap_pgv_not_available(self, mock_to_agraph, mock_pgv_module):
        """Test that generate_mindmap exits if pgv module is None (mocked as None)."""
        with patch('mindmap_generator.pgv', None), \
             patch('builtins.print') as mock_print:
            generate_mindmap([{"text":"test"}], "output.png")
            mock_print.assert_any_call("Error: pygraphviz is not installed or could not be imported. Cannot generate mind map.")
            mock_to_agraph.assert_not_called()


    def test_generate_mindmap_empty_data_structure(self, mock_to_agraph, mock_pgv_module):
        """Test generate_mindmap with an empty data structure."""
        mock_pgv_module.AGraph.return_value = create_mock_agraph() # Ensure pgv.AGraph() is mockable if called
        mock_to_agraph.return_value = create_mock_agraph()

        with patch('builtins.print') as mock_print:
            generate_mindmap([], "empty.png")
            # Check that "Input data structure is empty" was printed
            self.assertTrue(any("Input data structure is empty" in call.args[0] for call in mock_print.call_args_list))
            mock_to_agraph.assert_not_called()
            if mock_to_agraph.return_value.draw.called: # Should not be called
                mock_to_agraph.return_value.draw.assert_not_called()


    @patch('mindmap_generator._build_graph_recursive')
    def test_generate_mindmap_no_nodes_after_build(self, mock_build_empty, mock_to_agraph, mock_pgv_module):
        """Test generate_mindmap when data structure results in no graph nodes."""
        mock_pgv_module.AGraph.return_value = create_mock_agraph()
        mock_to_agraph.return_value = create_mock_agraph()
        
        def side_effect_empty_graph(data_structure, graph, parent_node_id=None, node_id_map=None):
            # This function effectively ensures the graph remains empty
            pass # Do not add nodes to graph
        mock_build_empty.side_effect = side_effect_empty_graph
            
        with patch('builtins.print') as mock_print:
            generate_mindmap([{"text": "dummy"}], "no_nodes.png")
            self.assertTrue(any("No nodes were added to the graph" in call.args[0] for call in mock_print.call_args_list))
            mock_to_agraph.assert_not_called()


    def test_generate_mindmap_successful_flow_default_style(self, mock_to_agraph, mock_pgv_module):
        """Test the successful flow with default styling."""
        sample_data = [{"text": "Root", "children": [{"text": "Child", "children": []}]}]
        
        mock_agraph_instance = create_mock_agraph()
        mock_to_agraph.return_value = mock_agraph_instance
        mock_pgv_module.AGraph.return_value = mock_agraph_instance # If direct AGraph() is called

        with patch('builtins.print'): # Suppress print statements
            generate_mindmap(sample_data, "output.png")

        mock_to_agraph.assert_called_once()
        nx_graph_passed = mock_to_agraph.call_args[0][0]
        self.assertIsInstance(nx_graph_passed, nx.DiGraph)
        self.assertEqual(nx_graph_passed.number_of_nodes(), 2)

        mock_agraph_instance.graph_attr.update.assert_called_with(ANY)
        mock_agraph_instance.node_attr.update.assert_called_with(ANY)
        mock_agraph_instance.edge_attr.update.assert_called_with(ANY)
        
        self.assertIn('rankdir', mock_agraph_instance.graph_attr.update.call_args[0][0])
        self.assertEqual(mock_agraph_instance.graph_attr.update.call_args[0][0]['rankdir'], 'TB')
        self.assertIn('shape', mock_agraph_instance.node_attr.update.call_args[0][0])
        self.assertEqual(mock_agraph_instance.node_attr.update.call_args[0][0]['shape'], 'box')

        self.assertTrue(mock_agraph_instance.get_node.call_count >= 2)
        mock_agraph_instance.draw.assert_called_once_with("output.png", prog='dot')

    def test_generate_mindmap_custom_style_application(self, mock_to_agraph, mock_pgv_module):
        """Test that custom styles correctly override defaults."""
        sample_data = [{"text": "Root", "children": []}]
        custom_styles = {
            'graph': {'rankdir': 'LR', 'bgcolor': 'yellow'},
            'node': {'shape': 'ellipse', 'fillcolor': 'red'},
            'edge': {'color': 'blue'}
        }
        
        mock_agraph_instance = create_mock_agraph()
        mock_to_agraph.return_value = mock_agraph_instance
        mock_pgv_module.AGraph.return_value = mock_agraph_instance

        with patch('builtins.print'):
            generate_mindmap(sample_data, "custom_output.png", style_attributes=custom_styles)

        mock_to_agraph.assert_called_once()

        updated_graph_attrs = mock_agraph_instance.graph_attr.update.call_args[0][0]
        self.assertEqual(updated_graph_attrs['rankdir'], 'LR')
        self.assertEqual(updated_graph_attrs['bgcolor'], 'yellow')
        self.assertIn('splines', updated_graph_attrs) 

        updated_node_attrs = mock_agraph_instance.node_attr.update.call_args[0][0]
        self.assertEqual(updated_node_attrs['shape'], 'ellipse')
        self.assertEqual(updated_node_attrs['fillcolor'], 'red')
        self.assertIn('style', updated_node_attrs)

        updated_edge_attrs = mock_agraph_instance.edge_attr.update.call_args[0][0]
        self.assertEqual(updated_edge_attrs['color'], 'blue')
        self.assertIn('arrowsize', updated_edge_attrs)

        mock_agraph_instance.draw.assert_called_once_with("custom_output.png", prog='dot')

    def test_generate_mindmap_to_agraph_conversion_failure(self, mock_to_agraph, mock_pgv_module):
        """Test handling of failure during NetworkX to AGraph conversion."""
        mock_to_agraph.side_effect = Exception("Conversion Error")
        mock_pgv_module.AGraph.return_value = create_mock_agraph() # Not strictly needed if to_agraph fails first

        sample_data = [{"text": "Root", "children": []}]
        with patch('builtins.print') as mock_print:
            generate_mindmap(sample_data, "error.png")
            self.assertTrue(any("Error converting NetworkX graph to AGraph" in call.args[0] for call in mock_print.call_args_list))
            # Draw should not be called on the instance if conversion fails before draw
            # mock_agraph_instance might not even be the one from this test if to_agraph is patched globally
            # Best to check if the mock_agraph_instance created for draw was called
            # However, if to_agraph fails, draw on its return value won't be called.
            # If to_agraph's mock itself had a draw method, we would check that.
            # For now, let's assume default mock behavior for draw on the instance.
            # If the code path exits before draw, this is fine.
            
            # Reset side_effect for other tests
            mock_to_agraph.side_effect = None 
            mock_to_agraph.return_value = create_mock_agraph() # Restore default mock

    def test_generate_mindmap_agraph_draw_failure(self, mock_to_agraph, mock_pgv_module):
        """Test handling of failure during AGraph.draw()."""
        sample_data = [{"text": "Root", "children": []}]
        
        mock_agraph_instance = create_mock_agraph()
        mock_agraph_instance.draw.side_effect = Exception("Graphviz Draw Error")
        mock_to_agraph.return_value = mock_agraph_instance
        mock_pgv_module.AGraph.return_value = mock_agraph_instance

        with patch('builtins.print') as mock_print:
            generate_mindmap(sample_data, "draw_error.png")
            self.assertTrue(any("Error rendering graph with PyGraphviz/Graphviz" in call.args[0] for call in mock_print.call_args_list))
            mock_agraph_instance.draw.assert_called_once()

if __name__ == '__main__':
    unittest.main()
