from langgraph.graph import END, START, StateGraph

from app.workflow.nodes import (
    WorkflowDependencies,
    approved_meeting_action,
    draft_reply,
    execute_tool,
    human_approval,
    risk_check,
    send_email,
    triage_email,
)
from app.workflow.state import MailOpsState


def build_graph(dependencies: WorkflowDependencies, checkpointer=None):
    """Compile the interruptible MailOps execution graph."""

    builder = StateGraph(MailOpsState)
    builder.add_node("triage_email", lambda state: triage_email(dependencies, state))
    builder.add_node("execute_tool", lambda state: execute_tool(dependencies, state))
    builder.add_node("draft_reply", lambda state: draft_reply(dependencies, state))
    builder.add_node("risk_check", lambda state: risk_check(dependencies, state))
    builder.add_node("human_approval", lambda state: human_approval(dependencies, state))
    builder.add_node("approved_meeting_action", lambda state: approved_meeting_action(dependencies, state))
    builder.add_node("send_email", lambda state: send_email(dependencies, state))
    builder.add_edge(START, "triage_email")
    builder.add_conditional_edges("triage_email", lambda state: END if state.get("error_message") else "execute_tool")
    builder.add_edge("execute_tool", "draft_reply")
    builder.add_edge("draft_reply", "risk_check")
    builder.add_conditional_edges("risk_check", lambda state: "human_approval" if state["requires_approval"] else "send_email")
    builder.add_conditional_edges("human_approval", lambda state: END if state.get("decision") == "reject" else "approved_meeting_action")
    builder.add_conditional_edges("approved_meeting_action", lambda state: END if state.get("error_message") else "send_email")
    builder.add_edge("send_email", END)
    return builder.compile(checkpointer=checkpointer)


__all__ = ["WorkflowDependencies", "build_graph"]
