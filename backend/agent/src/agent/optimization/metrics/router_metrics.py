"""Router accuracy metric for DSPy optimization."""

from agent.dspy_modules.agent_router import DiagramRouter


def router_accuracy_metric(example, prediction, trace=None) -> float:
    """Check if the router classified the request to the correct tool.

    Maps the predicted keyword to a tool name using DiagramRouter.TOOL_ROUTING,
    then compares with example.expected_route.

    Args:
        example: dspy.Example with expected_route field.
        prediction: Router prediction with diagram_type field.
        trace: Optional trace (unused).

    Returns:
        1.0 if correct, 0.0 otherwise.
    """
    expected_route = example.expected_route

    # Get the predicted keyword from the classifier
    predicted_keyword = getattr(prediction, "diagram_type", "").lower().strip()

    # Build keyword -> tool_name mapping from the router config
    keyword_to_tool = {}
    for tool_name, keywords in DiagramRouter.TOOL_ROUTING.items():
        for keyword in keywords:
            keyword_to_tool[keyword] = tool_name

    # Map predicted keyword to tool name
    predicted_route = keyword_to_tool.get(predicted_keyword, "fallback")

    return 1.0 if predicted_route == expected_route else 0.0
