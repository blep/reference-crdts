#!/usr/bin/env python3
"""Tracing script for CRDT operations, ported from trace.ts."""

from reference_crdts.crdts import new_doc, get_array, merge_into, local_insert, fugue


def main():
    # Simulate the operations from trace.ts
    # Using fugue algorithm as in the original

    # Create documents
    a = new_doc()
    b = new_doc()
    c = new_doc()

    # a.insert(0, 1) -> local_insert(a, 'A', 0, 1, fugue)
    local_insert(a, 'A', 0, 1, fugue)
    # a.insert(1, 2)
    local_insert(a, 'A', 1, 2, fugue)

    # merge(a, c) -> merge_into(fugue, a, c); merge_into(fugue, c, a)
    merge_into(fugue, a, c)
    merge_into(fugue, c, a)

    # b.insert(0, 6)
    local_insert(b, 'B', 0, 6, fugue)
    # c.insert(2, 7)
    local_insert(c, 'C', 2, 7, fugue)

    # merge(b, a)
    merge_into(fugue, b, a)
    merge_into(fugue, a, b)

    # b.insert(2, 14)
    local_insert(b, 'B', 2, 14, fugue)

    # Print b's document
    print("Document b after operations:")
    fugue.print_doc(b)

    # merge(c, b)
    merge_into(fugue, c, b)
    merge_into(fugue, b, c)

    print("Final document b:")
    fugue.print_doc(b)


if __name__ == "__main__":
    main()