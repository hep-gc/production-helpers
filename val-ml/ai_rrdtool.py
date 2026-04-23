import rrdtool
from pathlib import Path
import generate_db_meta as metadata
from pydantic import BaseModel
from typing import Annotated, Sequence, TypedDict, Literal
from difflib import get_close_matches
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
#from langchain_core.runnables import RunnableConfig

# -------------------- metadata  ---------------------------

METADATA = metadata.create_registry()
model= "qwen3:latest"
model_provider = "ollama"
# -------------------- tools -------------------------------
#query tool for metadata
class MetadataQuery(BaseModel):
    entity: Literal["cluster", "host", "metric"]
    cluster: str | list[str] | None=None
    host: str | list[str] |None=None

def validate_host(name: str, registry) -> str | list:
    """
    Validate host name.
    - if exact match → return name
    - if no match → return suggestions
    """
    if name in registry.hosts:
        return name

    suggestions = get_close_matches(name, registry.hosts.keys(), n=5, cutoff=0.4)
    return suggestions

def validate_cluster(name:str, registry)-> str |list:
    """
    Validate cluster name.
    - if exact match → return name
    - if no match → return suggestions
    """
    if name in registry.clusters:
        return name

    suggestions = get_close_matches(name, registry.clusters.keys(), n=5, cutoff=0.4)
    return suggestions

@tool
def query_metadata(query: MetadataQuery)->dict:
    """
    Query monitoring metadata registry.
    
    Call shape= query:{"entity": "cluster"}

    Always add query: at the beginning

    Examples:
    - list clusters= query: {"entity": "cluster"}
    - list hosts in cluster= query: {"entity": "host", "cluster": "BaBar"}
    - list metrics for host= query: {"entity": "metric", "host": "x"}
    """
    registry = METADATA
    query_result = {
        "clusters": [],
        "hosts": [],
        "metrics": []
    }

    if query.entity == "cluster":
        query_result["clusters"] = list(registry.clusters.keys())

    if query.entity == "host":
        clusters = []

        if query.cluster:
            if isinstance(query.cluster, list):
                clusters = query.cluster
            else:
                clusters = [query.cluster]

            for c in clusters:
                validated = validate_cluster(c, registry)

                if isinstance(validated, list):
                    return {"error": "cluster not found", "suggestions": validated}

                hosts = registry.clusters.get(validated, [])
                query_result["hosts"].append({
                    "cluster": validated,
                    "hosts": [h.name for h in hosts]
                })

        else:
            query_result["hosts"] = [h.name for h in registry.hosts.values()]

    if query.entity == "metric":
        if query.cluster:
            clusters = query.cluster if isinstance(query.cluster, list) else [query.cluster]

            for c in clusters:
                validated = validate_cluster(c, registry)

                if isinstance(validated, list):
                    return {"error": "cluster not found", "suggestions": validated}

                hosts = registry.clusters.get(validated, [])

                cluster_metrics = []

                for h in hosts:
                    host_meta = registry.hosts.get(h.name)
                    if host_meta:
                        cluster_metrics.extend([
                            {"host": h.name, "name": name, "path": str(meta.rrd_path)}
                            for name, meta in host_meta.metrics.items()
                        ])

                query_result["metrics"].append({
                    "cluster": validated,
                    "metrics": cluster_metrics
                })

        elif query.host:
            hosts = query.host if isinstance(query.host, list) else [query.host]

            for hname in hosts:
                validated = validate_host(hname, registry)

                if isinstance(validated, list):
                    return {"error": "host not found", "suggestions": validated}

                host_meta = registry.hosts.get(validated)

                if host_meta:
                    query_result["metrics"].append({
                        "host": validated,
                        "metrics": [
                            {"name": name, "path": str(meta.rrd_path)}
                            for name, meta in host_meta.metrics.items()
                        ]
                    })

        else:
            for h in registry.hosts.values():
                query_result["metrics"].append({
                    "host": h.name,
                    "metrics": [
                        {"name": name, "path": str(meta.rrd_path)}
                        for name, meta in h.metrics.items()
                    ]
                })

    return query_result

tools = [query_metadata]


# -------------------- llm --------------------------------------
llm = init_chat_model(model, model_provider=model_provider, temperature=0).bind_tools(tools)

# -------------------- agent state -------------------------------

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# -------------------- graph helper functions --------------------

def process(state: AgentState) -> AgentState:
    """node calls llm and answers user input"""
    system_prompt = SystemMessage(content = "You are an AI assistant with a tool to query the monitoring metadata registry, make as many tool calls as necesarry to answer questions as accurate as possible")
    response = llm.invoke([system_prompt] + state['messages'])
    return {'messages': [response]}

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "get_metadata"

# -------------------- graph ---------------------------------
graph = StateGraph(AgentState)
get_metadata = ToolNode(tools)
graph.add_node("get_metadata", get_metadata)
graph.add_node("agent_call_node", process)

graph.add_edge(START, "agent_call_node")
graph.add_edge("get_metadata", "agent_call_node")
graph.add_conditional_edges(
    "agent_call_node",
    should_continue,
)

agent = graph.compile()
# -------------------- streaming / viewing -------------------

def print_stream(stream):
    responses = None
    for s in stream:
        responses = s
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
    return responses
# -------------------- main ----------------------------------

def main():
    try:
        conversation =[]
        while True:
            user_input = input("Type to ask the llm: ")
            conversation.append(HumanMessage(content=user_input))
            inputs = {"messages": conversation}
            final_state=print_stream(agent.stream(inputs, stream_mode="values"))
            
            conversation=final_state["messages"]
    except KeyboardInterrupt:
         print("\nExiting program")

if __name__ == "__main__":
    main()



