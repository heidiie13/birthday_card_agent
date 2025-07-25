from core_agent.utils.nodes import (
    input_node,
    llm_node,
    dominant_color_node,
    merge_node,
    add_text_node,
)

from core_agent.utils.state import AgentState
from langgraph.graph import StateGraph, END

def build_birthday_card_graph() -> StateGraph:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("input", input_node)
    graph_builder.add_node("dominant_color", dominant_color_node)
    graph_builder.add_node("llm", llm_node)
    graph_builder.add_node("merge", merge_node)
    graph_builder.add_node("add_text", add_text_node)

    graph_builder.add_edge("input", "dominant_color")
    graph_builder.add_edge("dominant_color", "llm")
    graph_builder.add_edge("llm", "merge")
    graph_builder.add_edge("merge", "add_text")
    graph_builder.add_edge("add_text", END)

    graph_builder.set_entry_point("input")

    graph = graph_builder.compile()
    return graph


if __name__=="__main__":
    graph = build_birthday_card_graph() 
    test_input = {
        "full_name": "Nguyễn Văn A",
        "gender": "Nam",
        "birthday": "2000-01-01",
        "extra_requirements": "Hãy viết thư chúc sinh nhật với 8 dòng thơ đi",
        "background_path": "static/backgrounds/back_2.webp",
        "foreground_path": "static/foregrounds/fore_2.webp",
        "merged_image_path": r"D:\PRJ\birthday_card_agent\static\merged\14b1d18f133f4c3ab870f7eeba0a9891.png",
        "merge_position": "top",
        "merge_margin_ratio": 0.05,
        "aspect_ratio": 3/4,
        "merge_foreground_ratio": 0.6666666666666666,
        "font_size": 100,
    }
    
    result = graph.invoke(test_input)
    print(result)