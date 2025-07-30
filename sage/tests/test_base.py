"""Unit tests for core base components."""

import pytest
from sage.core.base import Node, Flow, SharedStore, AsyncNode


class TestSharedStore:
    """Test SharedStore functionality."""
    
    def test_get_set(self):
        """Test basic get/set operations."""
        store = SharedStore()
        
        # Set value
        store.set("key1", "value1")
        assert store.get("key1") == "value1"
        
        # Get with default
        assert store.get("nonexistent", "default") == "default"
    
    def test_dict_access(self):
        """Test dict-like access."""
        store = SharedStore()
        
        # Set via dict syntax
        store["key2"] = "value2"
        assert store["key2"] == "value2"
        
        # Get via dict syntax
        assert store.get("key2") == "value2"
    
    def test_update(self):
        """Test bulk update."""
        store = SharedStore()
        
        updates = {
            "key3": "value3",
            "key4": "value4"
        }
        store.update(updates)
        
        assert store.get("key3") == "value3"
        assert store.get("key4") == "value4"
    
    def test_listeners(self):
        """Test listener notifications."""
        store = SharedStore()
        notifications = []
        
        def listener(key, value):
            notifications.append((key, value))
        
        # Subscribe to changes
        store.subscribe("test_key", listener)
        
        # Trigger notification
        store.set("test_key", "test_value")
        
        assert len(notifications) == 1
        assert notifications[0] == ("test_key", "test_value")


class MockNode(Node):
    """Mock node for testing."""
    
    def __init__(self, name="mock"):
        super().__init__(name)
        self.prep_called = False
        self.exec_called = False
        self.post_called = False
    
    def prep(self, shared):
        self.prep_called = True
        return {"data": "prep"}
    
    def exec(self, data):
        self.exec_called = True
        return "exec_result"
    
    def post(self, shared, prep_res, exec_res):
        self.post_called = True
        return "next_action"


class TestNode:
    """Test Node base class."""
    
    def test_node_lifecycle(self):
        """Test node prep/exec/post lifecycle."""
        node = MockNode()
        store = SharedStore()
        
        action = node.run(store)
        
        assert node.prep_called
        assert node.exec_called
        assert node.post_called
        assert action == "next_action"
    
    def test_node_chaining_linear(self):
        """Test linear node chaining with >> operator."""
        node1 = MockNode("node1")
        node2 = MockNode("node2")
        
        node1 >> node2
        
        assert node1.default_next == node2
    
    def test_node_chaining_branching(self):
        """Test branching node chaining."""
        node1 = MockNode("node1")
        node2 = MockNode("node2")
        node3 = MockNode("node3")
        
        node1 >> {
            "action1": node2,
            "action2": node3
        }
        
        assert node1.next_nodes["action1"] == node2
        assert node1.next_nodes["action2"] == node3


class TestFlow:
    """Test Flow execution."""
    
    def test_flow_initialization(self):
        """Test flow initialization."""
        flow = Flow()
        assert flow.shared is not None
        assert isinstance(flow.shared, SharedStore)
        assert flow.start_node is None
        assert flow.history == []
    
    def test_flow_execution_linear(self):
        """Test linear flow execution."""
        # Create nodes
        node1 = MockNode("node1")
        node2 = MockNode("node2")
        
        # Create flow
        flow = Flow()
        flow.set_start(node1)
        
        # Chain nodes
        node1 >> node2
        
        # Override post to control flow
        def post1(shared, prep_res, exec_res):
            return None  # End flow after first node
        
        node1.post = post1
        
        # Run flow
        flow.run(max_steps=10)
        
        assert "node1" in flow.history
        assert node1.exec_called
    
    def test_flow_max_steps(self):
        """Test flow respects max_steps."""
        # Create self-looping node
        node = MockNode("loop")
        node >> node  # Points to itself
        
        flow = Flow()
        flow.set_start(node)
        
        # Run with limited steps
        flow.run(max_steps=3)
        
        assert len(flow.history) == 3
    
    def test_flow_branching(self):
        """Test branching flow execution."""
        node1 = MockNode("node1")
        node2 = MockNode("node2")
        node3 = MockNode("node3")
        
        # Set up branching
        node1 >> {
            "path1": node2,
            "path2": node3
        }
        
        # Override post to return specific action
        def post_branch(shared, prep_res, exec_res):
            return "path1"
        
        node1.post = post_branch
        
        # End nodes
        node2.post = lambda *args: None
        node3.post = lambda *args: None
        
        flow = Flow()
        flow.set_start(node1)
        flow.run()
        
        assert flow.history == ["node1", "node2"]