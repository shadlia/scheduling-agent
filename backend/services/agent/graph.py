from langgraph.graph import END, StateGraph
from services.agent.state import SchedulingState
from services.agent.nodes import greeting_node, collect_info_node, confirm_node, create_event_node
from services.agent.edges import router

def build_scheduling_graph() -> StateGraph:
    """Build and compile the LangGraph scheduling workflow."""
    graph = StateGraph(SchedulingState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("collect_info", collect_info_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("create_event", create_event_node)

    graph.set_conditional_entry_point(
        router,
        {
            "greeting": "greeting",
            "collect_info": "collect_info",
            "confirm": "confirm",
            "create_event": "create_event",
        }
    )
    
    # EVERY node should yield back to the user (END) after processing its logical step
    # The 'router' will send the NEXT user message to the correct node based on 'current_step'.
    graph.add_edge("greeting", END)
    graph.add_edge("collect_info", END)
    
    # Confirm either moves to create_event immediately (if confirmed) or yields to END (if user rejected/wants changes)
    graph.add_conditional_edges(
        "confirm",
        lambda state: "create_event" if state.confirmed else END,
        {
            "create_event": "create_event",
            END: END
        }
    )

    graph.add_edge("create_event", END)

    return graph.compile()

# Expose the compiled agent
scheduling_agent = build_scheduling_graph()
