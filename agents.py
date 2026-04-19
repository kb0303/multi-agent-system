from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# Model setup
# llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
def get_llm(model_name: str):
    return ChatGroq(model=model_name, temperature=0)

# 1st agent
def build_search_agent(llm):
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="You MUST use the web_search tool. Always return correct and working URLs. Do not answer from your own knowledge."
    )

# 2nd agent
def build_reader_agent(llm):
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="You MUST use the scrape_url tool. Always return the scraped content from the provided URL. Do not answer from your own knowledge., till you get the content."
    )
    
    
# writer chain
def get_writer_chain(llm):
    writer_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
        ("human", """Write a detailed research report on the topic below.

    Topic: {topic}

    Research Gathered:
    {research}

    Structure the report as:
    - Introduction
    - Key Findings (minimum 3 well-explained points)
    - Conclusion
    - Sources (list all URLs found in the research)

    Be detailed, factual and professional."""),
    ])

    return writer_prompt | llm | StrOutputParser()


# debate chain
def get_debate_chain(llm):
    debate_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert analyst capable of arguing both sides of a topic clearly and intelligently."),
        ("human", """
    Based on the research report below, generate a structured debate.

    Report:
    {report}

    Respond in this exact format (follow exactly, no markdown, no extra symbols):

    Optimist View:
    - Present the most positive, opportunity-focused perspective
    - Highlight benefits, growth, upside

    Skeptic View:
    - Present critical concerns, risks, and limitations
    - Challenge assumptions and highlight downsides

    Keep both sides balanced, realistic, and insightful.
    """),
    ])

    return debate_prompt | llm | StrOutputParser()

# critic_chain
def get_critic_chain(llm):
    critic_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a sharp and constructive research critic. Be honest and specific."),
        ("human", """Review the research report below and evaluate it strictly.

    Report:
    {report}

    Respond in this exact format:

    Score: X/10

    Strengths:
    - ...
    - ...

    Areas to Improve:
    - ...
    - ...

    One line verdict:
    ..."""),
    ])

    return critic_prompt | llm | StrOutputParser()