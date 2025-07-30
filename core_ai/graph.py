from core_ai.utils.nodes import (
    llm_node,
    dominant_color_node,
    merge_node,
    add_text_node,
)

from core_ai.utils.state import AgentState
from langgraph.graph import StateGraph

def build_birthday_card_graph() -> StateGraph:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("input", lambda state: state)
    graph_builder.add_node("dominant_color", dominant_color_node)
    graph_builder.add_node("llm", llm_node)
    graph_builder.add_node("merge", merge_node)
    graph_builder.add_node("add_text", add_text_node)

    graph_builder.add_edge("input", "dominant_color")
    graph_builder.add_edge("dominant_color", "llm")
    graph_builder.add_edge("llm", "merge")
    graph_builder.add_edge("merge", "add_text")
    graph_builder.add_edge("add_text", "__end__")

    graph_builder.set_entry_point("input")

    graph = graph_builder.compile()
    return graph

graph = build_birthday_card_graph()

if __name__=="__main__":
    graph = build_birthday_card_graph() 
    
    from PIL import Image

    import matplotlib.pyplot as plt
    import io
    
    mermaid_png = graph.get_graph().draw_mermaid_png()
    
    img = Image.open(io.BytesIO(mermaid_png))
    plt.imshow(img)
    plt.axis('off')
    plt.show()
    
    test_input = {
        "greeting_text_instructions": "Thiệp chúc mừng sinh nhật cho bé gái tên Linh, 8 tuổi, thích màu hồng và Hello Kitty",
        "background_path": "static/backgrounds/back_6.jpeg",
        "foreground_path": "static/foregrounds/fore_2.webp",
        "merged_image_path": "1.jpg",
    }
    
    result = graph.invoke(test_input)
    print(result)