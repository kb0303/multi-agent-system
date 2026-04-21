from agents import (
    get_llm,
    build_search_agent,
    build_reader_agent,
    get_writer_chain,
    get_debate_chain,
    get_critic_chain
)
from stream_manager import push_event
import asyncio

def stream_agent(agent, payload, emit, step):
    full_text = ""

    try:
        for chunk in agent.stream(payload):
            
            # 🔥 raw chunk dump (THIS is what you want)
            raw = str(chunk)

            emit({
                "type": "log",
                "data": f"[{step.upper()} RAW] {raw}\n"
            })

            # try extracting usable text
            content = ""

            if isinstance(chunk, dict):
                # LangGraph format: {"agent": {"messages": [...]}}
                for node_output in chunk.values():
                    if isinstance(node_output, dict) and "messages" in node_output:
                        msgs = node_output["messages"]
                        if msgs:
                            content = getattr(msgs[-1], "content", "") or ""
                            break
                # fallback for flat dicts
                if not content and "content" in chunk:
                    content = chunk["content"]
            else:
                content = str(chunk)

            if content:
                full_text += content
                emit({"type": "data_chunk", "step": step, "data": content})

    except Exception:
        result = agent.invoke(payload)
        content = result['messages'][-1].content

        emit({
            "type": "data_chunk",
            "step": step,
            "data": content
        })

        full_text = content

    return full_text

def run_research_pipeline(topic: str, model_name: str, session_id=None, loop=None) -> dict:
    
    def log(message):
        print(message)  # still print to terminal
        
        emit({
            "type": "log",
            "data": message + "\n"
        })

    def emit(data):
        asyncio.run_coroutine_threadsafe(
            push_event(session_id, data),
            loop
        )
            
    llm = get_llm(model_name)
    state = {}
    
    emit({"type": "pipeline_start"})
    
    # Step 1 - search agent working
    emit({"type": "step_start", "step": "search"})
    log("\n"+" ="*50)
    log("step 1 - search agent is working ...")
    log("="*50)
    
    search_agent = build_search_agent(llm)

    state["search_results"] = stream_agent(
        search_agent,
        {
            "messages": [("user", f"Find recent and reliable information about: {topic}")]
        },
        emit,
        "search"
    )

    emit({"type": "step_end", "step": "search"})

    log(f"\n Search Result :\n {state['search_results']}")

    
    # step 2 - reader agent working
    emit({"type": "step_start", "step": "reader"})
    log("\n"+" ="*50)
    log("step 2 - reader agent is scrapping top resources ...")
    log("="*50)
    
    reader_agent = build_reader_agent(llm)

    state["scraped_content"] = stream_agent(
        reader_agent,
        {
            "messages": [("user", 
                f"Based on the following search results about '{topic}',"
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        },
        emit,
        "reader"
    )

    emit({"type": "step_end", "step": "reader"})
    
    log(f"\n Scraped Content :\n {state['scraped_content']}")
    
    # step 3 - writer chain working
    emit({"type": "step_start", "step": "writer"})
    log("\n"+" ="*50)
    log("step 3 - writer chain is drafting the report ...")
    log("="*50)
    
    research_combined = (
        f"SEARCH RESULTS: \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"
    )
    
    writer = get_writer_chain(llm)

    report = ""

    for chunk in writer.stream({
        "topic": topic,
        "research": research_combined
    }):
        report += chunk
        emit({
            "type": "data_chunk",
            "step": "writer",
            "data": chunk
        })

    state["report"] = report
    
    emit({"type": "step_end", "step": "writer"})
    log(f"\n Final Report :\n {state['report']}")

    # step 4 - debate chain working
    emit({"type": "step_start", "step": "debate"})
    log("\n"+" ="*50)
    log("step 4 - debate chain is generating perspectives ...")
    log("="*50)

    debate_chain = get_debate_chain(llm)

    debate_text = ""

    for chunk in debate_chain.stream({
        "report": state["report"]
    }):
        debate_text += chunk
        emit({
            "type": "data_chunk",
            "step": "debate",
            "data": chunk
        })

    state["debate"] = debate_text
    
    # emit({
    #     "type": "data",
    #     "step": "debate",
    #     "data": state["debate"]
    # })

    emit({"type": "step_end", "step": "debate"})

    log(f"\n Debate Output :\n {state['debate']}")
    
    # step 5 - critic chain working
    emit({"type": "step_start", "step": "critic"})
    log("\n"+" ="*50)
    log("step 5 - critic chain is evaluating the report ...")
    log("="*50)

    critic = get_critic_chain(llm)

    feedback = ""
    try:
        for chunk in critic.stream({"report": state["report"]}):
            feedback += chunk
            emit({
                "type": "data_chunk",
                "step": "critic",
                "data": chunk
            })
    except:
        result = critic.invoke({"report": state["report"]})
        feedback = result

        emit({
            "type": "data",
            "step": "critic",
            "data": feedback
        })

    state["feedback"] = feedback
    emit({"type": "step_end", "step": "critic"})
    
    log(f"\n Feedback :\n {state['feedback']}")
    
    emit({"type": "done"})
    return state

if __name__ == "__main__":
    topic = input("Enter a research topic: ")
    run_research_pipeline(topic)
    
    