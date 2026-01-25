from available_nodes import *  # noqa
from diagrams import Cluster, Diagram, Edge, Node  # noqa


def AggregatorNode():
    return Node("", shape="plaintext", height="0.0", width="0.0")


default_graph_attr = {
    "concentrate": "true",
    "splines": "spline",
}

default_node_attr = {}

default_edge_attr = {}


def draw_diagram(**kwargs):
    graph_attr = dict(**default_graph_attr, **(kwargs.get("graph_attr", {})))
    node_attr = dict(**default_node_attr, **(kwargs.get("node_attr", {})))
    edge_attr = dict(**default_edge_attr, **(kwargs.get("edge_attr", {})))
    with Diagram(
        name=f"\n{kwargs.get('title')}",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
        show=False,
        direction=kwargs.get("direction", "LR"),
        filename=kwargs.get("filename"),
    ):
        exec(kwargs.get("code"))


if __name__ == "__main__":
    draw_diagram(
        title="Simple",
        code="""
user = User("User")
browser = Client("Browser")
with Cluster("Our VPC"):
    lb = LoadBalancing("Load Balancer")
    lb >> [Run("CloudRun Service\\n(Django server)"), Storage("GCS Bucket\\n(Static HTML)")]
user >> browser >> lb
""",
        filename="temp",
    )
