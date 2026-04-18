from agents import (
    get_llm,
    build_search_agent,
    build_reader_agent,
    get_writer_chain,
    get_debate_chain,
    get_critic_chain
)

def run_research_pipeline(topic: str, model_name: str) -> dict:

    llm = get_llm(model_name)
    state = {}
    
    # Step 1 - search agent working
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)
    
    search_agent = build_search_agent(llm)
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent and reliable information about: {topic}")]
    })
    state["search_results"] = search_result['messages'][-1].content

    print("\n Search Result :\n", state["search_results"])

    # step 2 - reader agent working
    print("\n"+" ="*50)
    print("step 2 - reader agent is scrapping top resources ...")
    print("="*50)
    
    reader_agent = build_reader_agent(llm)
    reader_result = reader_agent.invoke({
        "messages": [("user", 
            f"Based on the following search results about '{topic}',"
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })
    
    state["scraped_content"] = reader_result['messages'][-1].content
    
    print("\n Scraped Content :\n", state["scraped_content"])
    
    # step 3 - writer chain working
    print("\n"+" ="*50)
    print("step 3 - writer chain is drafting the report ...")
    print("="*50)
    
    research_combined = (
        f"SEARCH RESULTS: \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"
    )
    
    state["report"] = get_writer_chain(llm).invoke(
        {
            "topic": topic,
            "research": research_combined
        }
    )
    
    print("\n Final Report :\n", state["report"])

    # step 4 - debate chain working
    print("\n"+" ="*50)
    print("step 4 - debate chain is generating perspectives ...")
    print("="*50)

    state["debate"] = get_debate_chain(llm).invoke({
    "report": state["report"]
    })

    print("\n Debate Output :\n", state["debate"])
    
    # step 5 - critic chain working
    print("\n"+" ="*50)
    print("step 4 - critic chain is evaluating the report ...")
    print("="*50)
    
    state["feedback"] = get_critic_chain(llm).invoke(
        {
            "report": state["report"]
        }
    )
    
    print("\n Feedback :\n", state["feedback"])
    
    return state

if __name__ == "__main__":
    topic = input("Enter a research topic: ")
    run_research_pipeline(topic)
    
    