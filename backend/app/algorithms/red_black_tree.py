"""Manual Red-Black Tree for emergency request priority management.

Insertion, deletion, rotations, and fix-ups are O(log n). The tree stores
priority keys as ``(urgency_rank, created_timestamp, request_id)`` so higher
urgency wins and newer requests break ties.
"""

from dataclasses import dataclass
from datetime import datetime


RED = "RED"
BLACK = "BLACK"
URGENCY_RANK = {"NORMAL": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass
class PriorityRecord:
    request_id: int
    urgency: str
    created_at: datetime
    priority_score: int | None = None


class Node:
    def __init__(self, key=None, item=None, color=RED):
        self.key = key
        self.item = item
        self.color = color
        self.left = None
        self.right = None
        self.parent = None


class RedBlackTree:
    """A mutable priority tree with a black sentinel leaf node."""

    def __init__(self):
        self.nil = Node(color=BLACK)
        self.nil.left = self.nil.right = self.nil.parent = self.nil
        self.root = self.nil

    @staticmethod
    def priority_key(item):
        def value(name, default=None):
            if isinstance(item, dict):
                return item.get(name, default)
            return getattr(item, name, default)

        urgency = str(value("urgency", "NORMAL")).upper()
        if urgency not in URGENCY_RANK:
            raise ValueError("invalid urgency")
        created_at = value("created_at")
        if not isinstance(created_at, datetime):
            raise ValueError("created_at must be a datetime")
        request_id = value("request_id")
        if isinstance(request_id, bool) or not isinstance(request_id, int):
            raise ValueError("request_id must be an integer")
        score = value("priority_score")
        score = score if isinstance(score, int) else URGENCY_RANK[urgency]
        return URGENCY_RANK[urgency], created_at.timestamp(), request_id, score

    def _node_key(self, item, key):
        if key is not None:
            return key
        return self.priority_key(item)[:3]

    def left_rotate(self, node):
        pivot = node.right
        node.right = pivot.left
        if pivot.left != self.nil:
            pivot.left.parent = node
        pivot.parent = node.parent
        if node.parent == self.nil:
            self.root = pivot
        elif node == node.parent.left:
            node.parent.left = pivot
        else:
            node.parent.right = pivot
        pivot.left = node
        node.parent = pivot

    def right_rotate(self, node):
        pivot = node.left
        node.left = pivot.right
        if pivot.right != self.nil:
            pivot.right.parent = node
        pivot.parent = node.parent
        if node.parent == self.nil:
            self.root = pivot
        elif node == node.parent.right:
            node.parent.right = pivot
        else:
            node.parent.left = pivot
        pivot.right = node
        node.parent = pivot

    def insert(self, item, key=None):
        node = Node(self._node_key(item, key), item)
        node.left = node.right = self.nil
        parent = self.nil
        current = self.root
        while current != self.nil:
            parent = current
            if node.key == current.key:
                raise ValueError("duplicate priority key")
            current = current.left if node.key < current.key else current.right
        node.parent = parent
        if parent == self.nil:
            self.root = node
        elif node.key < parent.key:
            parent.left = node
        else:
            parent.right = node
        self._fix_insert(node)
        return node

    def _fix_insert(self, node):
        while node.parent.color == RED:
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                if uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    node.parent.parent.color = RED
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self.left_rotate(node)
                    node.parent.color = BLACK
                    node.parent.parent.color = RED
                    self.right_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                if uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    node.parent.parent.color = RED
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self.right_rotate(node)
                    node.parent.color = BLACK
                    node.parent.parent.color = RED
                    self.left_rotate(node.parent.parent)
        self.root.color = BLACK
        self.root.parent = self.nil

    def search(self, key):
        current = self.root
        while current != self.nil:
            if key == current.key:
                return current.item
            current = current.left if key < current.key else current.right
        return None

    def delete(self, key):
        node = self._find_node(key)
        if node == self.nil:
            return None
        removed_item = node.item
        replacement = node
        original_color = replacement.color
        if node.left == self.nil:
            child = node.right
            self._transplant(node, node.right)
        elif node.right == self.nil:
            child = node.left
            self._transplant(node, node.left)
        else:
            replacement = self._minimum(node.right)
            original_color = replacement.color
            child = replacement.right
            if replacement.parent == node:
                child.parent = replacement
            else:
                self._transplant(replacement, replacement.right)
                replacement.right = node.right
                replacement.right.parent = replacement
            self._transplant(node, replacement)
            replacement.left = node.left
            replacement.left.parent = replacement
            replacement.color = node.color
        if original_color == BLACK:
            self._fix_delete(child)
        return removed_item

    def _find_node(self, key):
        current = self.root
        while current != self.nil:
            if key == current.key:
                return current
            current = current.left if key < current.key else current.right
        return self.nil

    def _minimum(self, node):
        while node.left != self.nil:
            node = node.left
        return node

    def _transplant(self, first, second):
        if first.parent == self.nil:
            self.root = second
        elif first == first.parent.left:
            first.parent.left = second
        else:
            first.parent.right = second
        second.parent = first.parent

    def _fix_delete(self, node):
        while node != self.root and node.color == BLACK:
            if node == node.parent.left:
                sibling = node.parent.right
                if sibling.color == RED:
                    sibling.color = BLACK
                    node.parent.color = RED
                    self.left_rotate(node.parent)
                    sibling = node.parent.right
                if sibling.left.color == BLACK and sibling.right.color == BLACK:
                    sibling.color = RED
                    node = node.parent
                else:
                    if sibling.right.color == BLACK:
                        sibling.left.color = BLACK
                        sibling.color = RED
                        self.right_rotate(sibling)
                        sibling = node.parent.right
                    sibling.color = node.parent.color
                    node.parent.color = BLACK
                    sibling.right.color = BLACK
                    self.left_rotate(node.parent)
                    node = self.root
            else:
                sibling = node.parent.left
                if sibling.color == RED:
                    sibling.color = BLACK
                    node.parent.color = RED
                    self.right_rotate(node.parent)
                    sibling = node.parent.left
                if sibling.right.color == BLACK and sibling.left.color == BLACK:
                    sibling.color = RED
                    node = node.parent
                else:
                    if sibling.left.color == BLACK:
                        sibling.right.color = BLACK
                        sibling.color = RED
                        self.left_rotate(sibling)
                        sibling = node.parent.left
                    sibling.color = node.parent.color
                    node.parent.color = BLACK
                    sibling.left.color = BLACK
                    self.right_rotate(node.parent)
                    node = self.root
        node.color = BLACK

    def get_highest_priority(self):
        if self.root == self.nil:
            return None
        current = self.root
        while current.right != self.nil:
            current = current.right
        return current.item
