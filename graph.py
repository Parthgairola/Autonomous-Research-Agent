from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph , START , END
from fpdf import FPDF

# Load Environment Variables
load_dotenv()

# Model
model = ChatGroq(model="openai/gpt-oss-20b",temperature=0)

#Tools
#TavilySearch for General web search for current info, articles, and broad topics
web_search_tool = TavilySearch(
    max_results=2,
    search_depth="basic",
    include_raw_content=False
)


# All available tools
tools = [web_search_tool]


# States
class State(TypedDict):
    user_query : str
    data : str
    summary : str
    approved : str
    attempt : int

# Agent
agent_with_tools = create_agent(
    model=model,
    tools=tools,
    system_prompt="""

    You are an autonomous research agent.

    Your job is to gather reliable information for the user's query.
    Use available tools, explore relevant sources, and collect:
    - Key factual information
    - Source titles and URLs
    - Supporting content

    Present the collected data as raw findings only. Do not summarize, 
    interpret, or draw conclusions — a separate step will handle that.
    Use at most 2 search tool calls, then stop searching and present your findings.
    """
)


# Nodes

# Research Agent
def research_agent(state:State)-> dict:
    """Gathers Information from external sources based on user query """

    print("\nResearch Agent: Gathering information...")


    response= agent_with_tools.invoke({
        "messages":[
            {"role":"user","content":state["user_query"]}
        ]
    },config={"recursion_limit":15})
    print("Research completed.")
    return {"data":response["messages"][-1].content}


# Summarizer Node
def summarizer_node(state:State)->dict:
    """Removes irrelevant information and generates a final summary """

    attempt = state.get("attempt", 0) + 1


    print(f"Summarizer Node: Creating summary - Attempt {attempt}")

    prompt = f"""
        You are an autonomous research summarizer.

        Analyze the data and independently identify the most relevant
        information for the user's query. Remove irrelevant and duplicate content,
        combine related findings, and produce an accurate, concise summary.

        Include:
        1. Key Points
        2. Important Findings
        3. References / Sources
        4. Actionable Insights (if applicable)

        Use only the provided data. Do not invent facts or sources.

        Return clean plain text only. Do not use Markdown formatting.

        data : {state["data"]}

        """
    response = model.invoke(prompt)

    print("Summary generated.")
    return {"summary": response.content, "attempt": attempt}
    

# Review Node
def review_node(state:State)->dict:
    """"Checks whether Summary is relevant to user query or not  """

    print("Review Node: Reviewing summary...")

    prompt = f"""
    Review the summary against the user's original query.

    If the summary is relevant, directly answers the user's query,
    and contains sufficient information, return ONLY:
    YES

    If not, return:
    NO: followed by a short description of what needs improvement.

    User Query:
    {state["user_query"]}

    Summary:
    {state["summary"]}

    """

    response = model.invoke(prompt)

    print(f"Review result: {response.content}")
    return {"approved":response.content}


# Router
def router(state:State):
    """Routes the workflow based on the review node's YES/NO decision """

    if state["attempt"] > 2:
        return "approved"
    elif state["approved"] == "YES":
        return "approved"
    else:
        return "revise"


# Intialize Graph
graph = StateGraph(State)

# Add Nodes
graph.add_node("research_agent",research_agent)
graph.add_node("summarizer_node",summarizer_node)
graph.add_node("review_node",review_node)

# Add Edges
graph.add_edge(START , "research_agent")
graph.add_edge("research_agent", "summarizer_node")
graph.add_edge("summarizer_node", "review_node")
graph.add_conditional_edges("review_node",router,{"approved":END,"revise":"summarizer_node"})

# Compile Graph
app = graph.compile()

# PDF Generator
def generate_pdf(summary):
    """Generates PDF of the summary."""

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", size=12)

    # Handle unsupported characters
    summary = summary.encode("latin-1", "replace").decode("latin-1")

    # Add summary to PDF
    pdf.multi_cell(0, 8, summary)

    # Save PDF
    pdf.output("summary.pdf")
