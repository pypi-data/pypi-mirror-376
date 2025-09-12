from graphlib import TopologicalSorter, CycleError

from fairdomseek.types.attribute import AttrType


def safe_process_order(dependencies: dict) -> list:
    """
    Given a dict mapping each node → list of its prerequisites,
    returns a list of all nodes in a valid processing order
    (predecessors always before successors).
    Raises ValueError if a cycle is detected.
    """
    ts = TopologicalSorter(dependencies)
    try:
        # static_order() gives you one valid topological ordering
        return list(ts.static_order())
    except CycleError as e:
        # e.args[1] holds the cycle
        cycle = e.args[1]
        raise ValueError(f"Circular dependency detected: {cycle}") from None

def order_st_processing(sample_types):
    dependencies = {}
    idx = {}
    for st in sample_types:
        idx[st.title] = st
        dependencies[st.title] = set()
        for attr in st.attributes:
            if attr.type == AttrType.RegisteredSample or attr.type == AttrType.RegisteredSampleList:
                dependencies[st.title].add(attr.registered_sample_title)
    return [idx[name] for name in safe_process_order(dependencies)]
