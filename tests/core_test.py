"""Tests for reference CRDTs."""

import pytest
from reference_crdts.crdts import Doc, Item, Id, new_doc, get_array, integrate_yjs_mod, local_insert, merge_into, can_insert_now


def make_item(content, id_or_agent, origin_left, origin_right, am_seq, sync9_parent=None, sync9_insert_after=True):
    id_val = id_or_agent if isinstance(id_or_agent, tuple) else (id_or_agent, 0)
    return Item(
        content=content,
        id=id_val,
        originLeft=sync9_parent if False else origin_left,  # For now, assume not sync9
        originRight=origin_right,
        seq=am_seq,
        insertAfter=sync9_insert_after,
        isDeleted=False,
    )


# Stub for YjsMod algorithm
class YjsMod:
    def integrate(self, doc: Doc, new_item: Item, idx_hint=None):
        integrate_yjs_mod(doc, new_item, idx_hint or -1)

    def local_insert(self, doc: Doc, agent: str, pos: int, content):
        local_insert(doc, agent, pos, content, self)

    def print_doc(self, doc: Doc):
        pass


yjs_mod = YjsMod()


def test_smoke():
    doc = new_doc()
    yjs_mod.integrate(doc, make_item('a', ('A', 0), None, None, 0))
    yjs_mod.integrate(doc, make_item('b', ('A', 1), ('A', 0), None, 1))

    assert get_array(doc) == ['a', 'b']


def test_smoke_merge():
    doc = new_doc()
    yjs_mod.integrate(doc, make_item('a', ('A', 0), None, None, 0))
    yjs_mod.integrate(doc, make_item('b', ('A', 1), ('A', 0), None, 1))

    doc2 = new_doc()
    merge_into(yjs_mod, doc2, doc)
    assert get_array(doc2) == ['a', 'b']


def test_interleaving():
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
            yjs_mod.integrate(doc, op)

    assert get_array(doc) == ['a', 'a', 'a', 'b', 'b', 'b']