from typing import Annotated, Sequence, TypedDict, Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
#from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

# -------------------- db connection --------------------
DB_USER="CHANGE"
DB_HOST="CHANGE"
DB_PASS="CHANGE"
DB_NAME="CHANGE"
db = SQLDatabase.from_uri(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}")


# -------------------- llm ------------------------------
llm = init_chat_model("qwen3:latest",model_provider="ollama" ,temperature=0)

# -------------------- tools ---------------------------
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

for tool in tools:
    print(f"{tool.name}: {tool.description}\n")

get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")


def list_tables(state: MessagesState):
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")

    return {"messages": [tool_call_message, tool_message, response]}

def call_get_schema(state: MessagesState):
    llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}

generate_query_system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
""".format(
    dialect=db.dialect,
    top_k=5,
)


def generate_query(state: MessagesState):
    system_message = {
        "role": "system",
        "content": generate_query_system_prompt,
    }
    llm_with_tools = llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])

    return {"messages": [response]}

check_query_system_prompt = """
You are a SQL expert with a strong attention to detail.
Double check the {dialect} query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes,
just reproduce the original query.

You will call the appropriate tool to execute the query after running this check.
""".format(dialect=db.dialect)


def check_query(state: MessagesState):
    system_message = {
        "role": "system",
        "content": check_query_system_prompt,
    }

    # Generate an artificial user message to check
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id

    return {"messages": [response]}

# -------------------- agent state --------------------

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# -------------------- helper functions --------------------

def process(state: AgentState) -> AgentState:
    """node calls llm and answers user input"""
    system_prompt = SystemMessage(content = "You are an agent that interacts with a SQL database."
                                            "First list tables with sql_db_list_tables."
                                            "Only generate syntactically correct SELECT queries."
                                            "Never run INSERT/UPDATE/DELETE/DROP statements.")
    response = llm.invoke([system_prompt] + state['messages'], tools=tools)
    return {'messages': [response]}

def should_continue(state: MessagesState):
    messages = state['messages']
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "check_query"

# -------------------- graph --------------------
graph = StateGraph(MessagesState)
graph.add_node(list_tables)
graph.add_node(call_get_schema)
graph.add_node(get_schema_node, "get_schema")
graph.add_node(generate_query)
graph.add_node(check_query)
graph.add_node(run_query_node, "run_query")

graph.add_edge(START, "list_tables")
graph.add_edge("list_tables", "call_get_schema")
graph.add_edge("call_get_schema", "get_schema")
graph.add_edge("get_schema", "generate_query")
graph.add_conditional_edges(
    "generate_query",
    should_continue,
)
graph.add_edge("check_query", "run_query")
graph.add_edge("run_query", "generate_query")

agent = graph.compile()
# -------------------- streaming / viewing --------------------

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

def chat_mode():
    while True:
        user_input = input("say something: ")
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Stopping memory agent.")
            break
        inputs = {"messages": [HumanMessage(content=user_input)]}
        print_stream(agent.stream(inputs, stream_mode="values"))


# -------------------- main --------------------

def main():
    try:
        while True:
            user_input = input("Type 'chat' to ask the llm: ")
            if user_input.lower() == "chat":
                print("=================================Entered chat mode==============================")
                chat_mode()
    except KeyboardInterrupt:
         print("\nExiting program")

if __name__ == "__main__":

    display(Image(agent.get_graph().draw_mermaid_png()))
    main()
