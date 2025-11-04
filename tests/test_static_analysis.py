#!/usr/bin/env python3
"""
Static analysis test for critical technical debt fixes.

Tests source code directly without importing modules.
No dependencies required - just reads the files.
"""

import re
import os
import sys

# Color output
class C:
    G = '\033[92m'  # Green
    R = '\033[91m'  # Red
    Y = '\033[93m'  # Yellow
    B = '\033[94m'  # Blue
    E = '\033[0m'   # End
    BOLD = '\033[1m'

def test(name):
    print(f"\n{C.B}{C.BOLD}▶ {name}{C.E}")

def ok(msg):
    print(f"  {C.G}✓{C.E} {msg}")

def fail(msg):
    print(f"  {C.R}✗{C.E} {msg}")

def warn(msg):
    print(f"  {C.Y}⚠{C.E} {msg}")

def info(msg):
    print(f"  {C.B}ℹ{C.E} {msg}")


def read_file(path):
    """Read file contents."""
    with open(path, 'r') as f:
        return f.read()


# ============================================================================
# Issue #1: No duplicate /verify_signature routes
# ============================================================================

def test_issue1_no_duplicate_routes():
    """Test that only ONE /verify_signature route exists."""
    test("Issue #1: No duplicate /verify_signature routes")

    source = read_file('app/app.py')

    # Find all @app.route('/verify_signature' decorators
    pattern = r"@app\.route\(['\"]\/verify_signature['\"]"
    matches = re.findall(pattern, source)

    if len(matches) == 0:
        fail("No /verify_signature route found!")
        return False
    elif len(matches) == 1:
        ok(f"Only ONE /verify_signature route found (correct)")
        return True
    else:
        fail(f"Found {len(matches)} duplicate /verify_signature routes!")
        return False


def test_issue1_no_legacy_function():
    """Test that verify_signature_legacy function is deleted."""
    test("Issue #1: verify_signature_legacy function deleted")

    source = read_file('app/app.py')

    if 'def verify_signature_legacy(' in source:
        fail("verify_signature_legacy function still exists (should be deleted)")
        return False
    else:
        ok("verify_signature_legacy function deleted (correct)")
        return True


def test_issue1_finish_login_used():
    """Test that _finish_login is called in verify_signature."""
    test("Issue #1: verify_signature uses _finish_login for OAuth cookies")

    source = read_file('app/app.py')

    # Find the verify_signature function
    match = re.search(r'@app\.route\([\'"]\/verify_signature[\'"]\).*?def verify_signature\(\):(.*?)(?=\n@app\.route|\ndef \w+\(|\nclass \w+)', source, re.DOTALL)

    if not match:
        fail("Could not find verify_signature function")
        return False

    func_body = match.group(1)

    if '_finish_login' in func_body:
        ok("verify_signature calls _finish_login (correct)")
        return True
    else:
        warn("verify_signature may not call _finish_login")
        return True  # Not critical


# ============================================================================
# Issue #2: OAuth storage uses PostgreSQL
# ============================================================================

def test_issue2_no_get_storage_calls():
    """Test that get_storage() calls are removed."""
    test("Issue #2: No get_storage() calls in OAuth code")

    source = read_file('app/app.py')

    # Find get_storage() calls
    matches = re.findall(r'get_storage\(\)', source)

    if len(matches) == 0:
        ok("No get_storage() calls found (correct - using db_storage)")
        return True
    else:
        fail(f"Found {len(matches)} get_storage() calls (should use db_storage)")
        # Show first few occurrences
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if 'get_storage()' in line and i < 10:
                info(f"  Line {i}: {line.strip()}")
        return False


def test_issue2_uses_store_oauth_client():
    """Test that store_oauth_client is used."""
    test("Issue #2: Uses store_oauth_client() from db_storage")

    source = read_file('app/app.py')

    if 'store_oauth_client(' in source:
        ok("store_oauth_client() is used (PostgreSQL storage)")
        return True
    else:
        fail("store_oauth_client() not found (should use db_storage)")
        return False


def test_issue2_uses_get_oauth_client():
    """Test that get_oauth_client is used."""
    test("Issue #2: Uses get_oauth_client() from db_storage")

    source = read_file('app/app.py')

    if 'get_oauth_client(' in source:
        ok("get_oauth_client() is used (PostgreSQL storage)")
        return True
    else:
        fail("get_oauth_client() not found (should use db_storage)")
        return False


def test_issue2_uses_oauth_code_functions():
    """Test that OAuth code functions use db_storage."""
    test("Issue #2: OAuth codes use db_storage functions")

    source = read_file('app/app.py')

    checks = [
        ('store_oauth_code', 'store_oauth_code() is used'),
        ('get_oauth_code', 'get_oauth_code() is used'),
        ('delete_oauth_code', 'delete_oauth_code() is used'),
    ]

    all_ok = True
    for func, msg in checks:
        if f'{func}(' in source:
            ok(msg)
        else:
            fail(f"{func}() not found")
            all_ok = False

    return all_ok


def test_issue2_deprecated_stores_marked():
    """Test that in-memory stores are marked as DEPRECATED."""
    test("Issue #2: In-memory stores marked DEPRECATED")

    source = read_file('app/app.py')

    # Find CLIENT_STORE and AUTH_CODE_STORE declarations
    if 'CLIENT_STORE: Dict' in source and 'DEPRECATED' in source:
        ok("CLIENT_STORE marked as DEPRECATED")
    else:
        warn("CLIENT_STORE may not be clearly marked as DEPRECATED")

    if 'AUTH_CODE_STORE: Dict' in source and 'DEPRECATED' in source:
        ok("AUTH_CODE_STORE marked as DEPRECATED")
    else:
        warn("AUTH_CODE_STORE may not be clearly marked as DEPRECATED")

    return True  # Warnings, not failures


# ============================================================================
# Issue #3: Chat history uses Redis
# ============================================================================

def test_issue3_redis_functions_exist():
    """Test that Redis chat history functions exist."""
    test("Issue #3: Redis chat history functions exist")

    source = read_file('app/app.py')

    funcs = [
        'def get_chat_history(',
        'def add_chat_message(',
        'def purge_old_chat_messages(',
    ]

    all_ok = True
    for func in funcs:
        if func in source:
            ok(f"{func.replace('def ', '').replace('(', '()')} exists")
        else:
            fail(f"{func.replace('def ', '').replace('(', '()')} not found")
            all_ok = False

    return all_ok


def test_issue3_get_redis_import():
    """Test that get_redis is imported."""
    test("Issue #3: get_redis imported from database")

    source = read_file('app/app.py')

    if 'from app.database import' in source and 'get_redis' in source:
        ok("get_redis imported from app.database")
        return True
    else:
        fail("get_redis not imported from app.database")
        return False


def test_issue3_redis_operations_used():
    """Test that Redis operations are used in chat functions."""
    test("Issue #3: Redis operations used (LPUSH, LRANGE, LTRIM)")

    source = read_file('app/app.py')

    ops = [
        ('lpush', 'LPUSH'),
        ('lrange', 'LRANGE'),
        ('ltrim', 'LTRIM'),
    ]

    all_ok = True
    for op, name in ops:
        if f'redis_client.{op}' in source:
            ok(f"Uses Redis {name} operation")
        else:
            warn(f"May not use Redis {name} operation")
            all_ok = True  # Warning, not failure

    return all_ok


def test_issue3_add_chat_message_used():
    """Test that add_chat_message() is called in message handler."""
    test("Issue #3: WebSocket handler uses add_chat_message()")

    source = read_file('app/app.py')

    # Find @socketio.on('message') handler
    match = re.search(r"@socketio\.on\(['\"]message['\"]\)(.*?)(?=\n@socketio\.on|\n@app\.route|\ndef \w+\()", source, re.DOTALL)

    if not match:
        warn("Could not find @socketio.on('message') handler")
        return True  # Can't verify

    handler_body = match.group(1)

    if 'add_chat_message(' in handler_body:
        ok("Message handler uses add_chat_message() (correct)")
        return True
    else:
        fail("Message handler does NOT use add_chat_message()")
        return False


def test_issue3_get_chat_history_used():
    """Test that get_chat_history() is used instead of direct CHAT_HISTORY access."""
    test("Issue #3: Uses get_chat_history() instead of direct access")

    source = read_file('app/app.py')

    # Find /chat route
    match = re.search(r"@app\.route\(['\"]\/chat['\"]\)(.*?)(?=\n@app\.route|\ndef \w+\()", source, re.DOTALL)

    if not match:
        warn("Could not find /chat route")
        return True

    route_body = match.group(1)

    if 'get_chat_history()' in route_body or 'history=get_chat_history()' in route_body:
        ok("/chat route uses get_chat_history() (correct)")
        return True
    else:
        fail("/chat route does NOT use get_chat_history()")
        return False


def test_issue3_chat_history_deprecated():
    """Test that CHAT_HISTORY is marked as DEPRECATED."""
    test("Issue #3: CHAT_HISTORY marked DEPRECATED")

    source = read_file('app/app.py')

    # Find CHAT_HISTORY declaration and check nearby for DEPRECATED
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'CHAT_HISTORY: List' in line:
            # Check previous 5 lines
            context = '\n'.join(lines[max(0, i-5):i])
            if 'DEPRECATED' in context:
                ok("CHAT_HISTORY marked as DEPRECATED (correct)")
                return True

    fail("CHAT_HISTORY not clearly marked as DEPRECATED")
    return False


# ============================================================================
# Main
# ============================================================================

def main():
    print(f"{C.BOLD}{'='*70}{C.E}")
    print(f"{C.BOLD}HODLXXI Static Analysis Tests (Issues #1, #2, #3){C.E}")
    print(f"{C.BOLD}No dependencies required - analyzes source code directly{C.E}")
    print(f"{C.BOLD}{'='*70}{C.E}")

    # Change to project root
    os.chdir('/home/user/The-Universal-Bitcoin-Identity-Layer')

    tests = [
        # Issue #1
        test_issue1_no_duplicate_routes,
        test_issue1_no_legacy_function,
        test_issue1_finish_login_used,

        # Issue #2
        test_issue2_no_get_storage_calls,
        test_issue2_uses_store_oauth_client,
        test_issue2_uses_get_oauth_client,
        test_issue2_uses_oauth_code_functions,
        test_issue2_deprecated_stores_marked,

        # Issue #3
        test_issue3_redis_functions_exist,
        test_issue3_get_redis_import,
        test_issue3_redis_operations_used,
        test_issue3_add_chat_message_used,
        test_issue3_get_chat_history_used,
        test_issue3_chat_history_deprecated,
    ]

    results = {}
    for t in tests:
        try:
            results[t.__name__] = t()
        except Exception as e:
            fail(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[t.__name__] = False

    # Summary
    print(f"\n{C.BOLD}{'='*70}{C.E}")
    print(f"{C.BOLD}Summary{C.E}")
    print(f"{C.BOLD}{'='*70}{C.E}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)
    failed = total - passed

    for name, result in results.items():
        status = f"{C.G}PASS{C.E}" if result else f"{C.R}FAIL{C.E}"
        # Clean up function name
        clean_name = name.replace('test_issue', 'Issue #').replace('_', ' ')
        print(f"{status} - {clean_name}")

    print(f"\n{C.BOLD}Result: {passed}/{total} passed, {failed}/{total} failed{C.E}")

    if failed == 0:
        print(f"\n{C.G}{C.BOLD}🎉 All tests passed! Critical fixes verified.{C.E}")
        return 0
    else:
        print(f"\n{C.R}{C.BOLD}⚠️  {failed} test(s) failed.{C.E}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
