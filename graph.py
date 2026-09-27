from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_community.tools import StackExchangeTool
from langchain_community.utilities import StackExchangeAPIWrapper
from langchain_community.tools import YouTubeSearchTool
from langgraph.graph import StateGraph , START , END
from fpdf import FPDF

# Load Environment Variables
load_dotenv()

# Model
model = ChatGroq(model="openai/gpt-oss-20b",temperature=0)

#Tools
#TavilySearch for General web search for current info, articles, and broad topics
web_search_tool = TavilySearch(
    max_results=5,
    search_depth="basic",
    include_raw_content=False
)

#StackExchangeTool for queries regarding programming errors
stackexchange_tool = StackExchangeTool(api_wrapper=StackExchangeAPIWrapper())

# YoutubeSearchTool for queries regarding tutorial/how-to videos - returns titles + links
youtube_search_tool = YouTubeSearchTool()

# All available tools
tools = [web_search_tool,stackexchange_tool,youtube_search_tool]


# States
class State(TypedDict):
    user_query : str
    data : str
    summary : str
    approved : str
    feedback :str

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
    })
    print("Research completed.")
    return {"data":response["messages"][-1].content}


# Summarizer Agent
def summarizer_agent(state:State)->dict:
    """Removes irrelevant information and generates a final summary """

    print("Summarizer Agent: Creating summary...")

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
    return {"summary":response.content}
    

# Review Agent
def review_agent(state:State)->dict:
    """"Checks whether Summary is relevant to user query or not  """

    print("Review Agent: Reviewing summary...")

    prompt = f"""
    Review the summary against the user's original query.

    Your response MUST be exactly one word: YES or NO.

    Return YES if the summary is relevant, directly answers the user's query,
    and contains sufficient information.

    Return NO if the summary is irrelevant, incomplete,
    or does not directly answer the user's query.

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
    """Routes the workflow based on the review agent's YES/NO decision """

    if state["approved"]=="YES":
        return "approved"
    else :
        return "revise"


# Intialize Graph
graph = StateGraph(State)

# Add Nodes
graph.add_node("research_agent",research_agent)
graph.add_node("summarizer_agent",summarizer_agent)
graph.add_node("review_agent",review_agent)

# Add Edges
graph.add_edge(START , "research_agent")
graph.add_edge("research_agent", "summarizer_agent")
graph.add_edge("summarizer_agent", "review_agent")
graph.add_conditional_edges("review_agent",router,{"approved":END,"revise":"summarizer_agent"})

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
