# Python Port Plan for Reference CRDTs

## Project Overview

Port of TypeScript reference CRDT implementations (Yjs, Automerge, Sync9, Fugue) to type-annotated Python 3.13. This is intended as a readable reference implementation for learning and testing, not for production use.

## Target File Structure

```
reference-crdts/
├── .github/
│   └── copilot-instructions.md          # Already exists
├── reference_crdts/
│   ├── __init__.py                       # Empty (with docstring only)
│   ├── types.py                          # Type definitions (Id, Version, Item, Doc, Algorithm)
│   ├── core.py                           # Core CRDT implementation
│   ├── algorithms.py                     # Algorithm objects (yjs, automerge, sync9, fugue, etc.)
│   └── utils.py                          # Helper functions (getArray, mergeInto, etc.)
├── tests/
│   ├── __init__.py                       # Empty
│   ├── core_test.py                      # Main test suite
│   └── conftest.py                       # pytest fixtures
├── README.md                             # Update with Python instructions
├── pyproject.toml                        # Python project configuration
├── requirements.txt                      # Runtime dependencies (empty - no deps needed)
├── requirements-dev.txt                  # Development dependencies (pytest, mypy)
└── .gitignore                            # Add Python-specific ignores

# Keep original TypeScript files for reference
bench.ts
crdts.ts
test.ts
...
```

## Porting Steps (Incremental, Test-Driven)

### Step 1: Minimal Setup to Run First Test
**Goal: Get pytest running with one passing test ASAP**

**Source:** Setup files + minimal from `crdts.ts` (lines 1-100)

1. Create minimal directory structure:
   ```bash
   mkdir reference_crdts tests
   touch reference_crdts/__init__.py tests/__init__.py
   ```

2. Create `requirements-dev.txt`:
   ```
   pytest>=7.0
   ```

3. Create `.gitignore` additions:
   ```
   __pycache__/
   *.pyc
   .pytest_cache/
   .mypy_cache/
   *.egg-info/
   ```

4. Create `reference_crdts/crdts.py` with minimal types:
   - **From `crdts.ts` lines 14-90**: Port basic type definitions:
     - `Id = tuple[str, int]`
     - `Version = dict[str, int]`
     - `Item[T]` dataclass
     - `Doc[T]` dataclass
   - `new_doc()` function
   - `get_array()` function (from line 176)

5. Create `tests/core_test.py` with ONE simple test:
   - **From `test.ts` lines 70-76**: Port `test_smoke()` only
   - Create `make_item()` helper (from lines 14-25)
   - Create stub for one algorithm (YjsMod)

6. **RUN: `pytest -v`** → Should have 1 test that fails (integrate not implemented yet)

### Step 2: Implement YjsMod Algorithm (First Working Test)
**Goal: Get first test passing**

**Source:** `crdts.ts` lines 100-250 (helpers) + lines 245-298 (YjsMod integrate)

7. Add to `reference_crdts/crdts.py`:
   - **Lines 100-106**: Port `id_eq()` and `id_eq2()` helpers
   - **Lines 110-148**: Port `find_item2()` and `find_item()` with hit/miss tracking
   - **Lines 245-298**: Port `integrate_yjs_mod()` function

8. Create simple Algorithm dataclass and `yjs_mod` instance

9. **RUN: `pytest -v`** → Should have 1 passing test! ✅

### Step 3: Add More Core Helpers (Enable More Tests)
**Goal: Support smoke_merge and basic operations**

**Source:** `crdts.ts` lines 150-244

10. Add to `reference_crdts/crdts.py`:
    - **Lines 162-170**: Port `find_item_at_pos()`
    - **Lines 173-187**: Port `local_insert()` function
    - **Lines 197-207**: Port `local_delete()` 
    - **Lines 214-224**: Port `is_in_version()` and `can_insert_now()`
    - **Lines 226-244**: Port `merge_into()`

11. Update Algorithm dataclass to include `local_insert` method

12. Port from `test.ts`:
    - **Lines 79-88**: Add `test_smoke_merge()`
    - **Lines 90-108**: Add `test_interleaving()`

13. **RUN: `pytest -v`** → Should have 3 passing tests for YjsMod ✅

### Step 4: Add Remaining Integration Functions
**Goal: Support all algorithms**

**Source:** `crdts.ts` lines 299-end

14. Add to `reference_crdts/crdts.py`:
    - **Lines 381-441**: Port `integrate_yjs()`
    - **Lines 443-501**: Port `integrate_rga_smol()` (Automerge)
    - **Lines 503-588**: Port `integrate_sync9()`
    - **Lines 304-379**: Port `integrate_fugue()`

15. Add `local_insert_sync9()` (lines 189-212)

16. Create all algorithm instances:
    - `yjs_mod`, `yjs`, `automerge`, `sync9`, `fugue`, `fugue_max`
    - Each with proper `local_insert`, `integrate`, `ignore_tests`

17. **RUN: `pytest -v`** → All algorithms with basic tests ✅

### Step 5: Port All Test Cases
**Goal: Complete test coverage**

**Source:** `test.ts` entire file

18. Port all remaining tests from `test.ts`:
    - **Lines 14-42**: Port helper functions (`make_item`, `integrate_fuzz_once`, `integrate_fuzz`)
    - **Lines 110-365**: Port all test cases:
      - `test_interleaving_backward()`
      - `test_interleaving_backward2()`
      - `test_with_tails()`
      - `test_with_tails2()`
      - `test_concurrent_delete()`
      - `test_rle_insert()`
      - ... (all other tests)

19. Use `@pytest.mark.parametrize` to run each test against all algorithms

20. Implement per-algorithm skipping using `ignore_tests` lists

21. **RUN: `pytest -v`** → Full test suite passing! ✅

### Step 6: Add Debugging and Polish
**Goal: Make it pleasant to use**

**Source:** `crdts.ts` various sections

22. Add to `reference_crdts/crdts.py`:
    - **Lines 210-242**: Port `print_doc()` function (simplified, no chalk)
    - **Lines 668-670**: Port `print_debug_stats()`

23. Add `Algorithm.print_doc` method to each algorithm

24. Create `reference_crdts/__init__.py` with exports:
    ```python
    """Reference CRDT implementations (Yjs, Automerge, Sync9, Fugue)."""
    from reference_crdts.crdts import (
        # Types
        Id, Version, Item, Doc,
        # Functions
        new_doc, get_array, local_delete, merge_into,
        # Algorithms
        yjs, yjs_mod, automerge, sync9, fugue, fugue_max,
    )
    ```

25. **RUN: `pytest -v` and `mypy reference_crdts/`** → All clean! ✅

### Step 7: Documentation
**Goal: Usable by others**

26. Update `README.md`:
    - Add Python setup section:
      ```bash
      # Python version
      pip install -r requirements-dev.txt
      pytest
      ```
    - Add Python usage example
    - Keep TypeScript info

27. Create `pyproject.toml` (minimal, for metadata only)

28. Add docstrings to main functions

29. **Final check: `pytest -v`** → Everything works! 🎉

## Key Translation Notes

### Naming Conventions
- TypeScript camelCase → Python snake_case
  - `originLeft` → `origin_left`
  - `isDeleted` → `is_deleted`
  - `localInsert` → `local_insert`
  - `newDoc` → `new_doc`

### Type System
- TypeScript interfaces → Python `@dataclass` or `Protocol`
- TypeScript generics `<T>` → Python `[T]` with `from typing import Generic, TypeVar`
- TypeScript `type` aliases → Python `TypeAlias`
- Nullable types `| null` → `| None`
- Arrays `T[]` → `list[T]`
- Objects `Record<K, V>` → `dict[K, V]`

### Syntax Differences
- TypeScript `===` → Python `==`
- TypeScript `!==` → Python `!=`
- Array methods:
  - `.push()` → `.append()`
  - `.splice(idx, 0, item)` → `.insert(idx, item)`
  - `.splice(idx, 1)` → `.pop(idx)` or `del arr[idx]`
  - `.findIndex()` → Use enumerate or list comprehension
- No need for TypeScript `assert` import - use Python's built-in `assert`
- No chalk for colors - use plain text or simple ANSI codes (optional)

### Special Considerations
- Global state (hits/misses counters) → Module-level variables
- Optional parameters with defaults work similarly
- Python doesn't have method binding with `this:` - use regular methods

### Testing Differences
- TypeScript custom test runner → pytest
- Manual `test()` wrapper → pytest discovers `test_*` functions
- Custom assertions → use pytest's assert with helpful messages
- Skip tests using `@pytest.mark.skip` or `@pytest.mark.skipif`

## Non-Goals (Out of Scope)

- RLE optimization (rle.ts) - keep simple for reference
- Benchmarking (bench.ts) - focus on correctness
- Trace replay (trace.ts) - can add later if needed
- Integration with real Yjs/Automerge - this is standalone
- Performance optimization - readability over speed
- Encoding/decoding support - reference implementation only

## Success Criteria

1. ✅ All TypeScript test cases ported to pytest
2. ✅ Tests pass for all algorithms (respecting ignore_tests)
3. ✅ Full type annotations with mypy passing
4. ✅ Code is readable and well-documented
5. ✅ Project follows Python best practices (PEP 8, etc.)
6. ✅ README has clear Python usage instructions
7. ✅ Can run tests with simple `pytest` command

## Estimated Effort

- Phase 1 (Setup): 30 minutes
- Phase 2 (Types): 30 minutes
- Phase 3 (Core): 2-3 hours (most complex part)
- Phase 4 (Algorithms): 30 minutes
- Phase 5 (Tests): 2-3 hours
- Phase 6 (Polish): 1 hour

**Total: ~6-8 hours** for complete, well-tested port
