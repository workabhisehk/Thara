"""
Hybrid routing system for Parlant and LangGraph.
Allows using both frameworks simultaneously based on message complexity.
"""

from agents_hybrid.router import handle_message_hybrid, route_message

__all__ = ["handle_message_hybrid", "route_message"]

