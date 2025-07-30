"""Core abstractions for SAGE - following PocketFlow's minimalist design."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
import asyncio
from dataclasses import dataclass, field
from .persistence import PersistenceProvider, JSONPersistence, AgentFork


class SharedStore:
    """Central state store for agent communication with persistence."""
    
    def __init__(self, persistence: Optional[PersistenceProvider] = None):
        self._store: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self.persistence = persistence or JSONPersistence()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from store."""
        return self._store.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in store and notify listeners."""
        self._store[key] = value
        self._notify_listeners(key, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple values at once."""
        for key, value in updates.items():
            self.set(key, value)
    
    def subscribe(self, key: str, callback: Callable) -> None:
        """Subscribe to changes for a specific key."""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
    
    def _notify_listeners(self, key: str, value: Any) -> None:
        """Notify all listeners for a key."""
        if key in self._listeners:
            for callback in self._listeners[key]:
                callback(key, value)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return self._store[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like assignment."""
        self.set(key, value)


class Node(ABC):
    """Base class for all agent nodes."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.next_nodes: Dict[str, 'Node'] = {}
        self.default_next: Optional['Node'] = None
    
    @abstractmethod
    def prep(self, shared: SharedStore) -> Dict[str, Any]:
        """Prepare data from shared store."""
        pass
    
    @abstractmethod
    def exec(self, data: Dict[str, Any]) -> Any:
        """Execute node logic."""
        pass
    
    @abstractmethod
    def post(self, shared: SharedStore, prep_res: Dict[str, Any], exec_res: Any) -> str:
        """Post-process and return next action."""
        pass
    
    def run(self, shared: SharedStore) -> Optional[str]:
        """Run the complete node cycle."""
        prep_res = self.prep(shared)
        exec_res = self.exec(prep_res)
        action = self.post(shared, prep_res, exec_res)
        return action
    
    def __rshift__(self, other):
        """Override >> operator for flow definition."""
        if isinstance(other, dict):
            # Branching: node >> {"action1": node1, "action2": node2}
            self.next_nodes = other
        else:
            # Linear: node1 >> node2
            self.default_next = other
        return other


class AsyncNode(Node):
    """Base class for async nodes."""
    
    @abstractmethod
    async def exec_async(self, data: Dict[str, Any]) -> Any:
        """Async execution."""
        pass
    
    async def run_async(self, shared: SharedStore) -> Optional[str]:
        """Run the async node cycle."""
        prep_res = self.prep(shared)
        exec_res = await self.exec_async(prep_res)
        action = self.post(shared, prep_res, exec_res)
        return action


@dataclass
class Flow:
    """Manages node execution flow."""
    
    shared: SharedStore = field(default_factory=SharedStore)
    start_node: Optional[Node] = None
    current_node: Optional[Node] = None
    history: List[str] = field(default_factory=list)
    
    def set_start(self, node: Node) -> None:
        """Set the starting node."""
        self.start_node = node
        self.current_node = node
    
    def run(self, max_steps: int = 100) -> None:
        """Run the flow synchronously."""
        if not self.start_node:
            raise ValueError("No start node set")
        
        self.current_node = self.start_node
        steps = 0
        
        while self.current_node and steps < max_steps:
            self.history.append(self.current_node.name)
            
            # Run current node
            action = self.current_node.run(self.shared)
            
            # Determine next node
            if action and action in self.current_node.next_nodes:
                # Branching based on action
                self.current_node = self.current_node.next_nodes[action]
            elif self.current_node.default_next:
                # Default next node
                self.current_node = self.current_node.default_next
            else:
                # No next node, flow ends
                self.current_node = None
            
            steps += 1
        
        if steps >= max_steps:
            print(f"Warning: Flow exceeded max steps ({max_steps})")
    
    async def run_async(self, max_steps: int = 100) -> None:
        """Run the flow asynchronously."""
        if not self.start_node:
            raise ValueError("No start node set")
        
        self.current_node = self.start_node
        steps = 0
        
        while self.current_node and steps < max_steps:
            self.history.append(self.current_node.name)
            
            # Run current node
            if isinstance(self.current_node, AsyncNode):
                action = await self.current_node.run_async(self.shared)
            else:
                action = self.current_node.run(self.shared)
            
            # Determine next node
            if action and action in self.current_node.next_nodes:
                self.current_node = self.current_node.next_nodes[action]
            elif self.current_node.default_next:
                self.current_node = self.current_node.default_next
            else:
                self.current_node = None
            
            steps += 1