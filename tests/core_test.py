"""Tests for reference CRDTs."""

import pytest
from reference_crdts.crdts import (
    Doc, Item, Id, new_doc, get_array, integrate_yjs_mod, local_insert,
    merge_into, can_insert_now, yjs_mod, yjs, automerge, sync9, fugue, fugue_max
)


def make_item(content, id_or_agent, origin_left, origin_right, am_seq, sync9_parent=None, sync9_insert_after=True, algorithm=None):
    id_val = id_or_agent if isinstance(id_or_agent, tuple) else (id_or_agent, 0)
    is_sync9 = algorithm and hasattr(algorithm, 'integrate') and algorithm.integrate.__name__ == 'integrate_sync9'
    final_origin_left = sync9_parent if is_sync9 else origin_left
    return Item(
        content=content,
        id=id_val,
        originLeft=final_origin_left,
        originRight=origin_right,
        seq=am_seq,
        insertAfter=sync9_insert_after,
        isDeleted=False,
    )


@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_smoke(algorithm):
    doc = new_doc()
    algorithm.integrate(doc, make_item('a', ('A', 0), None, None, 0))
    algorithm.integrate(doc, make_item('b', ('A', 1), ('A', 0), None, 1))

    assert get_array(doc) == ['a', 'b']


@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_smoke_merge(algorithm):
    doc = new_doc()
    algorithm.integrate(doc, make_item('a', ('A', 0), None, None, 0))
    algorithm.integrate(doc, make_item('b', ('A', 1), ('A', 0), None, 1))

    doc2 = new_doc()
    merge_into(algorithm, doc2, doc)
    assert get_array(doc2) == ['a', 'b']


@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_interleaving(algorithm):
    ops = [
        make_item('a', ('A', 0), None, None, 0),
        make_item('a', ('A', 1), ('A', 0), None, 1),
        make_item('a', ('A', 2), ('A', 1), None, 2),

        make_item('b', ('B', 0), None, None, 0),
        make_item('b', ('B', 1), ('B', 0), None, 1),
        make_item('b', ('B', 2), ('B', 1), None, 2),
    ]

    # Simple integration in order
    doc = new_doc()
    for op in ops:
        if can_insert_now(op, doc):
            algorithm.integrate(doc, op)

@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_interleaving_backward(algorithm):
    if algorithm.ignore_tests and 'test_interleaving_backward' in algorithm.ignore_tests:
        pytest.skip("Test ignored for this algorithm")
    
    ops = [
        make_item('a', ('A', 0), None, None, 0),
        make_item('a', ('A', 1), None, ('A', 0), 1),
        make_item('a', ('A', 2), None, ('A', 1), 2),

        make_item('b', ('B', 0), None, None, 0),
        make_item('b', ('B', 1), None, ('B', 0), 1),
        make_item('b', ('B', 2), None, ('B', 1), 2),
    ]

    # Simple integration in order
    doc = new_doc()
    for op in ops:
        if can_insert_now(op, doc):
            algorithm.integrate(doc, op)

@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_concurrent_a_vs_b(algorithm):
    a = make_item('a', 'A', None, None, 0)
    b = make_item('b', 'B', None, None, 0)
    
    # Try integrating in both orders
    doc1 = new_doc()
    algorithm.integrate(doc1, a)
    algorithm.integrate(doc1, b)
    result1 = get_array(doc1)
    
    doc2 = new_doc()
    algorithm.integrate(doc2, b)
    algorithm.integrate(doc2, a)
    result2 = get_array(doc2)
    
    # Both should give the same result
    assert result1 == result2 == ['a', 'b']


@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_interleaving_forward2(algorithm):
    ops = [
        make_item('a', ('A', 0), None, None, 0),
        make_item('a', ('X', 0), ('A', 0), None, 1),
        make_item('a', ('Y', 0), ('X', 0), None, 2),

        make_item('b', ('B', 0), None, None, 0),
        make_item('b', ('C', 0), ('B', 0), None, 1),
        make_item('b', ('D', 0), ('C', 0), None, 2),
    ]

    # Simple integration in order
    doc = new_doc()
    for op in ops:
        if can_insert_now(op, doc):
            algorithm.integrate(doc, op)

    assert get_array(doc) == ['a', 'a', 'a', 'b', 'b', 'b']


@pytest.mark.parametrize("algorithm", [yjs_mod, yjs, automerge, sync9, fugue, fugue_max])
def test_with_tails(algorithm):
    if algorithm.ignore_tests and 'test_with_tails' in algorithm.ignore_tests:
        pytest.skip("Test ignored for this algorithm")
    
    ops = [
        make_item('a', ('A', 0), None, None, 0, algorithm=algorithm),
        make_item('a0', ('A', 1), None, ('A', 0), 1, ('A', 0), False, algorithm),  # left of a
        make_item('a1', ('A', 2), ('A', 0), None, 2, algorithm=algorithm),  # right of a

        make_item('b', ('B', 0), None, None, 0, algorithm=algorithm),
        make_item('b0', ('B', 1), None, ('B', 0), 1, ('B', 0), False, algorithm),  # left of b
        make_item('b1', ('B', 2), ('B', 0), None, 2, algorithm=algorithm),  # right of b
    ]

    # Simple integration in order
    doc = new_doc()
    for op in ops:
        if can_insert_now(op, doc):
            algorithm.integrate(doc, op)

    assert get_array(doc) == ['a0', 'a', 'a1', 'b0', 'b', 'b1']