from core_agent.utils.nodes import (
    input_node,
    merge_foreground_background_node,
    dominant_color_node,
    llm_suggest_text_and_color,
    add_text_node,
    feedback_node,
    tool_node
)
from core_agent.utils.state import AgentState
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition

def build_birthday_card_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("input", input_node)
    graph.add_node("merge_foreground_background", merge_foreground_background_node)
    graph.add_node("dominant_color", dominant_color_node)
    graph.add_node("llm_suggest_text_and_color", llm_suggest_text_and_color)
    graph.add_node("add_text", add_text_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("tools", tool_node)

    graph.add_edge("input", "merge_foreground_background")
    graph.add_edge("merge_foreground_background", "dominant_color")
    graph.add_edge("dominant_color", "llm_suggest_text_and_color")
    graph.add_edge("llm_suggest_text_and_color", "add_text")
    graph.add_edge("add_text", "feedback")
    graph.add_conditional_edges("feedback", tools_condition)

    graph.set_entry_point("input")
    graph.set_finish_point("add_text")
    return graph

def run_birthday_card_graph(input_data: dict, thread_id: str = None) -> dict:
    graph = build_birthday_card_graph()
    compiled_graph = graph.compile(checkpoint=MemorySaver())
    
    # from PIL import Image

    # import matplotlib.pyplot as plt
    # import io
    
    # mermaid_png = compiled_graph.get_graph().draw_mermaid_png()
    
    # img = Image.open(io.BytesIO(mermaid_png))
    # plt.imshow(img)
    # plt.axis('off')
    # plt.show()
    
    config = {"configurable": {"thread_id": thread_id}}
    
    if "messages" not in input_data:
        input_data["messages"] = []
    result = compiled_graph.invoke(input_data, config=config)
    return result

if __name__=="__main__":
    # Example input for testing
    test_input = {
        "full_name": "Alice Nguyen",
        "gender": "female",
        "birthday": "1995-05-20",
        "recipient": "friend",
        "style": "poem",
        "background_path": "static/backgrounds/back_30.png",
        "foreground_path": "static/foregrounds/fore_3.webp",
        "merged_image_path": "",
        "messages": [],
    }
    
    result = run_birthday_card_graph(test_input)
    print(result)