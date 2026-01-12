"""Reference CRDT implementations in Python."""

from dataclasses import dataclass
from typing import TypeVar, Generic, List, Dict, Tuple, Optional

T = TypeVar('T')

Id = Tuple[str, int]
Version = Dict[str, int]


@dataclass
class Item(Generic[T]):
    content: Optional[T]
    id: Id
    originLeft: Optional[Id]
    originRight: Optional[Id]
    seq: int
    insertAfter: bool
    isDeleted: bool


@dataclass
class Doc(Generic[T]):
    content: List[Item[T]]
    version: Version
    length: int
    maxSeq: int


def new_doc() -> Doc[T]:
    return Doc(
        content=[],
        version={},
        length=0,
        maxSeq=0,
    )


def get_array(doc: Doc[T]) -> List[T]:
    return [item.content for item in doc.content if not item.isDeleted and item.content is not None]


# Helpers
def id_eq(a: Optional[Id], b: Optional[Id]) -> bool:
    return a == b or (a is not None and b is not None and a[0] == b[0] and a[1] == b[1])


def id_eq2(a: Optional[Id], agent: str, seq: int) -> bool:
    return a is not None and a[0] == agent and a[1] == seq


hits = 0
misses = 0


def find_item2(doc: Doc[T], needle: Optional[Id], at_end: bool = False, idx_hint: int = -1) -> int:
    if needle is None:
        return -1
    else:
        agent, seq = needle
        # Optimization with hint
        if idx_hint >= 0 and idx_hint < len(doc.content):
            hint_item = doc.content[idx_hint]
            if (not at_end and id_eq2(hint_item.id, agent, seq)) or \
               (hint_item.content is not None and at_end and id_eq2(hint_item.id, agent, seq)):
                global hits
                hits += 1
                return idx_hint

        global misses
        misses += 1
        for i, item in enumerate(doc.content):
            if (not at_end and id_eq2(item.id, agent, seq)) or \
               (item.content is not None and at_end and id_eq2(item.id, agent, seq)):
                return i
        raise ValueError('Could not find item')


def find_item(doc: Doc[T], needle: Optional[Id], idx_hint: int = -1) -> int:
    return find_item2(doc, needle, False, idx_hint)


def integrate_yjs_mod(doc: Doc[T], new_item: Item[T], idx_hint: int = -1) -> None:
    last_seen = doc.version.get(new_item.id[0], -1)
    if new_item.id[1] != last_seen + 1:
        raise ValueError('Operations out of order')
    doc.version[new_item.id[0]] = new_item.id[1]

    left = find_item(doc, new_item.originLeft, idx_hint - 1)
    dest_idx = left + 1
    right = len(doc.content) if new_item.originRight is None else find_item(doc, new_item.originRight, idx_hint)
    scanning = False

    i = dest_idx
    while True:
        if not scanning:
            dest_idx = i
        if i == len(doc.content):
            break
        if i == right:
            break  # No ambiguity / concurrency. Insert here.

        other = doc.content[i]

        oleft = find_item(doc, other.originLeft, idx_hint - 1)
        oright = len(doc.content) if other.originRight is None else find_item(doc, other.originRight, idx_hint)

        # The logic below summarizes to:
        # if (oleft < left || (oleft === left && oright === right && newItem.id[0] < o.id[0])) break
        # if (oleft === left) scanning = oright < right

        if oleft < left:
            # Top row. Insert, insert, arbitrary (insert)
            break
        elif oleft == left:
            # Middle row.
            if oright < right:
                # This is tricky. We're looking at an item we *might* insert after - but we can't tell yet!
                scanning = True
                i += 1
                continue
            elif oright == right:
                # Raw conflict. Order based on user agents.
                if new_item.id[0] < other.id[0]:
                    break
                else:
                    scanning = False
                    i += 1
                    continue
            else:  # oright > right
                scanning = False
                i += 1
                continue
        else:  # oleft > left
            # Bottom row. Arbitrary (skip), skip, skip
            i += 1
            continue

    # We've found the position. Insert here.
    doc.content.insert(dest_idx, new_item)
    if not new_item.isDeleted:
        doc.length += 1


def integrate_yjs(doc: Doc[T], new_item: Item[T], idx_hint: int = -1) -> None:
    last_seen = doc.version.get(new_item.id[0], -1)
    if new_item.id[1] != last_seen + 1:
        raise ValueError('Operations out of order')
    doc.version[new_item.id[0]] = new_item.id[1]

    left = find_item(doc, new_item.originLeft, idx_hint - 1)
    dest_idx = left + 1
    right = len(doc.content) if new_item.originRight is None else find_item(doc, new_item.originRight, idx_hint)
    scanning = False

    i = dest_idx
    while True:
        if not scanning:
            dest_idx = i
        if i == len(doc.content):
            break
        if i == right:
            break  # No ambiguity / concurrency. Insert here.

        other = doc.content[i]

        oleft = find_item(doc, other.originLeft, idx_hint - 1)
        oright = len(doc.content) if other.originRight is None else find_item(doc, other.originRight, idx_hint)

        if oleft < left:
            break
        elif oleft == left:
            if new_item.id[0] > other.id[0]:
                scanning = False
                i += 1
                continue
            elif oright == right:
                break
            else:
                scanning = True
                i += 1
                continue
        else:
            i += 1
            continue

    # We've found the position. Insert here.
    doc.content.insert(dest_idx, new_item)
    if not new_item.isDeleted:
        doc.length += 1


def integrate_rga_smol(doc: Doc[T], new_item: Item[T], idx_hint: int = -1) -> None:
    agent, seq = new_item.id
    parent = find_item(doc, new_item.originLeft, idx_hint - 1)

    # Scan to find the insert location
    i = parent + 1
    while i < len(doc.content):
        o = doc.content[i]
        if new_item.seq > o.seq:
            break  # Optimization
        oparent = find_item(doc, o.originLeft, idx_hint - 1)

        if oparent < parent or (oparent == parent and new_item.seq == o.seq and agent < o.id[0]):
            break
        i += 1

    # Insert at position i
    doc.content.insert(i, new_item)
    doc.version[agent] = seq
    doc.maxSeq = max(doc.maxSeq, new_item.seq)
    if not new_item.isDeleted:
        doc.length += 1


def find_item_at_pos(doc: Doc[T], pos: int, stick_end: bool = False) -> int:
    i = 0
    for i in range(len(doc.content)):
        item = doc.content[i]
        if stick_end and pos == 0:
            return i
        elif item.isDeleted or item.content is None:
            continue
        elif pos == 0:
            return i
        pos -= 1

    if pos == 0:
        return i + 1  # Since i is the last index in the loop
    else:
        raise ValueError('past end of the document')


def local_insert(doc: Doc[T], agent: str, pos: int, content: T, algorithm) -> None:
    i = find_item_at_pos(doc, pos)
    new_item = Item(
        content=content,
        id=(agent, doc.version.get(agent, -1) + 1),
        isDeleted=False,
        originLeft=doc.content[i - 1].id if i > 0 else None,
        originRight=doc.content[i].id if i < len(doc.content) else None,
        insertAfter=True,
        seq=doc.maxSeq + 1,
    )
    algorithm.integrate(doc, new_item, i)


def local_delete(doc: Doc[T], agent: str, pos: int) -> None:
    # This is very incomplete.
    idx = find_item_at_pos(doc, pos)
    item = doc.content[idx]
    if not item.isDeleted:
        item.isDeleted = True
        doc.length -= 1


def is_in_version(id_: Optional[Id], version: Version) -> bool:
    if id_ is None:
        return True
    seq = version.get(id_[0])
    return seq is not None and seq >= id_[1]


def can_insert_now(op: Item[T], doc: Doc[T]) -> bool:
    return (not is_in_version(op.id, doc.version) and
            (op.id[1] == 0 or is_in_version((op.id[0], op.id[1] - 1), doc.version)) and
            is_in_version(op.originLeft, doc.version) and
            is_in_version(op.originRight, doc.version))


def merge_into(algorithm, dest: Doc[T], src: Doc[T]) -> None:
    # The list of operations we need to integrate
    missing = [op for op in src.content if op.content is not None and not is_in_version(op.id, dest.version)]
    remaining = len(missing)

    while remaining > 0:
        merged_on_this_pass = 0
        for i in range(len(missing)):
            op = missing[i]
            if op is None or not can_insert_now(op, dest):
                continue
            algorithm.integrate(dest, op)
            missing[i] = None
            remaining -= 1
            merged_on_this_pass += 1

        if merged_on_this_pass == 0:
            raise AssertionError("No progress in merge_into")


def integrate_sync9(doc: Doc[T], new_item: Item[T], idx_hint: int = -1) -> None:
    agent, seq = new_item.id
    last_seen = doc.version.get(agent, -1)
    if seq != last_seen + 1:
        raise ValueError('Operations out of order')
    doc.version[agent] = seq

    parent_idx = find_item2(doc, new_item.originLeft, new_item.insertAfter, idx_hint - 1)
    dest_idx = parent_idx + 1

    if parent_idx >= 0 and new_item.originLeft and not new_item.insertAfter and doc.content[parent_idx].content is not None:
        # Split left item to add null content item to the set
        doc.content.insert(parent_idx, Item(
            content=None,
            id=doc.content[parent_idx].id,
            originLeft=doc.content[parent_idx].originLeft,
            originRight=doc.content[parent_idx].originRight,
            seq=doc.content[parent_idx].seq,
            insertAfter=doc.content[parent_idx].insertAfter,
            isDeleted=doc.content[parent_idx].isDeleted,
        ))
        # We can skip the loop because we know we're an only child.
    else:
        while dest_idx < len(doc.content):
            other = doc.content[dest_idx]
            oparent_idx = find_item2(doc, other.originLeft, other.insertAfter, idx_hint - 1)

            if oparent_idx < parent_idx:
                break
            elif oparent_idx == parent_idx:
                if new_item.id[0] < other.id[0]:
                    break
                else:
                    dest_idx += 1
                    continue
            else:
                dest_idx += 1
                continue

    # Insert here
    doc.content.insert(dest_idx, new_item)
    if not new_item.isDeleted and new_item.content is not None:
        doc.length += 1


def integrate_fugue(doc: Doc[T], new_item: Item[T], idx_hint: int = -1) -> None:
    last_seen = doc.version.get(new_item.id[0], -1)
    if new_item.id[1] != last_seen + 1:
        raise ValueError('Operations out of order')
    doc.version[new_item.id[0]] = new_item.id[1]

    end_idx = len(doc.content)
    scanning = False

    left_idx = find_item(doc, new_item.originLeft, idx_hint - 1)
    dest_idx = left_idx + 1

    def get_right_parent_idx(item: Item[T]) -> int:
        right_idx = end_idx if item.originRight is None else find_item(doc, item.originRight, idx_hint)
        right = doc.content[right_idx] if right_idx < end_idx else None
        return end_idx if right is None or not id_eq(right.originLeft, item.originLeft) else right_idx

    right_p_idx = get_right_parent_idx(new_item)

    i = dest_idx
    while True:
        if not scanning:
            dest_idx = i
        if i == end_idx:
            break  # Hit the end

        other = doc.content[i]
        if id_eq(other.id, new_item.originRight):
            break  # Hit originRight

        oleft_idx = find_item(doc, other.originLeft, idx_hint - 1)
        oright_p_idx = get_right_parent_idx(other)

        if oleft_idx < left_idx or (oleft_idx == left_idx and oright_p_idx == right_p_idx and new_item.id[0] < other.id[0]):
            break
        if oleft_idx == left_idx:
            scanning = oright_p_idx < right_p_idx
        i += 1

    # Insert here
    doc.content.insert(dest_idx, new_item)
    if not new_item.isDeleted:
        doc.length += 1


def local_insert_sync9(doc: Doc[T], agent: str, pos: int, content: T, algorithm) -> None:
    i = find_item_at_pos(doc, pos, True)
    parent_id_base = doc.content[i - 1].id if i > 0 else None
    origin_left = None if parent_id_base is None else (parent_id_base[0], parent_id_base[1])
    insert_after = True

    while True:
        next_item = doc.content[i] if i < len(doc.content) else None
        if next_item is None or not id_eq(next_item.originLeft, parent_id_base):
            break

        parent_id_base = next_item.id
        origin_left = (next_item.id[0], next_item.id[1])
        insert_after = False
        if next_item.content is not None:
            break
        i += 1

    new_item = Item(
        content=content,
        id=(agent, doc.version.get(agent, -1) + 1),
        isDeleted=False,
        originLeft=origin_left,
        originRight=None,
        seq=0,
        insertAfter=insert_after,
    )
    algorithm.integrate(doc, new_item, i)


@dataclass
class Algorithm(Generic[T]):
    local_insert: callable
    integrate: callable
    print_doc: callable
    ignore_tests: Optional[List[str]] = None


# Algorithm instances
def print_doc_default(doc: Doc[T]) -> None:
    pass


yjs_mod = Algorithm(
    local_insert=local_insert,
    integrate=integrate_yjs_mod,
    print_doc=print_doc_default,
)

yjs = Algorithm(
    local_insert=local_insert,
    integrate=integrate_yjs,
    print_doc=print_doc_default,
    ignore_tests=['test_with_tails2'],
)

automerge = Algorithm(
    local_insert=local_insert,
    integrate=integrate_rga_smol,
    print_doc=print_doc_default,
    ignore_tests=[
        'test_interleaving_backward',
        'test_interleaving_backward2',
        'test_with_tails',
        'test_with_tails2'
    ],
)

sync9 = Algorithm(
    local_insert=local_insert_sync9,
    integrate=integrate_sync9,
    print_doc=print_doc_default,
)

fugue = Algorithm(
    local_insert=local_insert,
    integrate=integrate_fugue,
    print_doc=print_doc_default,
)

fugue_max = Algorithm(
    local_insert=local_insert,
    integrate=integrate_yjs_mod,  # Same as yjs_mod
    print_doc=print_doc_default,
)