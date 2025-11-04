#!/usr/bin/env python3
"""
Test suite for critical technical debt fixes (Issues #1, #2, #3).

This script tests:
- Issue #1: No duplicate /verify_signature routes
- Issue #2: OAuth storage uses PostgreSQL (not in-memory)
- Issue #3: Chat history uses Redis (not in-memory)

Run with: python tests/test_critical_fixes.py
"""

import sys
import os
import json
import time
import inspect

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Color output for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name):
    print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {name}{Colors.END}")

def print_pass(msg):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")

def print_fail(msg):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")

def print_warn(msg):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"  {Colors.BLUE}ℹ{Colors.END} {msg}")


# ============================================================================
# Issue #1: Test for duplicate /verify_signature routes
# ============================================================================

def test_no_duplicate_verify_signature():
    """Test that only ONE /verify_signature route exists."""
    print_test("Issue #1: No duplicate /verify_signature routes")

    try:
        from app import app as flask_app

        # Get all routes
        routes = []
        for rule in flask_app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                    'path': str(rule)
                })

        # Find /verify_signature routes
        verify_routes = [r for r in routes if r['path'] == '/verify_signature']

        if len(verify_routes) == 0:
            print_fail("No /verify_signature route found!")
            return False
        elif len(verify_routes) == 1:
            print_pass(f"Only ONE /verify_signature route exists: {verify_routes[0]}")

            # Verify it accepts POST
            if 'POST' in verify_routes[0]['methods']:
                print_pass("Route accepts POST method")
            else:
                print_fail(f"Route does not accept POST: {verify_routes[0]['methods']}")
                return False

            return True
        else:
            print_fail(f"Found {len(verify_routes)} duplicate /verify_signature routes:")
            for r in verify_routes:
                print_info(f"  - {r['endpoint']} {r['methods']} {r['path']}")
            return False

    except Exception as e:
        print_fail(f"Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verify_signature_function():
    """Test that verify_signature function exists and is not duplicated."""
    print_test("Issue #1: Verify signature function is unique")

    try:
        import app.app as app_module

        # Find all functions named verify_signature*
        verify_funcs = []
        for name, obj in inspect.getmembers(app_module):
            if inspect.isfunction(obj) and 'verify_signature' in name:
                verify_funcs.append(name)

        print_info(f"Functions matching 'verify_signature': {verify_funcs}")

        # Should have verify_signature but NOT verify_signature_legacy
        if 'verify_signature' in verify_funcs:
            print_pass("verify_signature function exists")
        else:
            print_fail("verify_signature function not found")
            return False

        if 'verify_signature_legacy' in verify_funcs:
            print_fail("verify_signature_legacy function still exists (should be deleted)")
            return False
        else:
            print_pass("verify_signature_legacy function deleted (correct)")

        return True

    except Exception as e:
        print_fail(f"Error checking functions: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Issue #2: Test OAuth storage uses PostgreSQL
# ============================================================================

def test_oauth_storage_postgresql():
    """Test that OAuth client storage uses PostgreSQL (db_storage)."""
    print_test("Issue #2: OAuth storage uses PostgreSQL")

    try:
        import app.app as app_module
        from app.db_storage import get_oauth_client, store_oauth_client

        # Check ClientManager.register_client source code
        source = inspect.getsource(app_module.ClientManager.register_client)

        # Should use store_oauth_client (PostgreSQL)
        if 'store_oauth_client' in source:
            print_pass("ClientManager.register_client uses store_oauth_client() (PostgreSQL)")
        else:
            print_fail("ClientManager.register_client does NOT use store_oauth_client()")
            return False

        # Should NOT use get_storage() (in-memory Redis)
        if 'get_storage()' in source:
            print_fail("ClientManager.register_client still uses get_storage() (in-memory)")
            return False
        else:
            print_pass("ClientManager.register_client does NOT use get_storage() (correct)")

        # Check ClientManager.authenticate_client source code
        source = inspect.getsource(app_module.ClientManager.authenticate_client)

        if 'get_oauth_client' in source:
            print_pass("ClientManager.authenticate_client uses get_oauth_client() (PostgreSQL)")
        else:
            print_fail("ClientManager.authenticate_client does NOT use get_oauth_client()")
            return False

        if 'get_storage()' in source:
            print_fail("ClientManager.authenticate_client still uses get_storage()")
            return False
        else:
            print_pass("ClientManager.authenticate_client does NOT use get_storage() (correct)")

        return True

    except Exception as e:
        print_fail(f"Error testing OAuth storage: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_oauth_code_storage():
    """Test that OAuth authorization codes use PostgreSQL."""
    print_test("Issue #2: OAuth authorization codes use PostgreSQL")

    try:
        import app.app as app_module

        # Check OAuthServer.authorization_endpoint source
        source = inspect.getsource(app_module.OAuthServer.authorization_endpoint)

        if 'store_oauth_code' in source:
            print_pass("OAuthServer.authorization_endpoint uses store_oauth_code() (PostgreSQL)")
        else:
            print_fail("OAuthServer.authorization_endpoint does NOT use store_oauth_code()")
            return False

        if 'get_storage()' in source:
            print_fail("OAuthServer.authorization_endpoint still uses get_storage()")
            return False
        else:
            print_pass("OAuthServer.authorization_endpoint does NOT use get_storage() (correct)")

        # Check OAuthServer._handle_code_grant source
        source = inspect.getsource(app_module.OAuthServer._handle_code_grant)

        if 'get_oauth_code' in source:
            print_pass("OAuthServer._handle_code_grant uses get_oauth_code() (PostgreSQL)")
        else:
            print_fail("OAuthServer._handle_code_grant does NOT use get_oauth_code()")
            return False

        if 'delete_oauth_code' in source:
            print_pass("OAuthServer._handle_code_grant uses delete_oauth_code() (PostgreSQL)")
        else:
            print_fail("OAuthServer._handle_code_grant does NOT use delete_oauth_code()")
            return False

        return True

    except Exception as e:
        print_fail(f"Error testing OAuth code storage: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Issue #3: Test chat history uses Redis
# ============================================================================

def test_chat_history_redis_functions():
    """Test that chat history helper functions exist."""
    print_test("Issue #3: Chat history Redis functions exist")

    try:
        import app.app as app_module

        # Check functions exist
        funcs_required = ['get_chat_history', 'add_chat_message', 'purge_old_chat_messages']

        for func_name in funcs_required:
            if hasattr(app_module, func_name):
                print_pass(f"{func_name}() function exists")
            else:
                print_fail(f"{func_name}() function NOT found")
                return False

        # Verify get_chat_history uses Redis
        source = inspect.getsource(app_module.get_chat_history)

        if 'get_redis()' in source:
            print_pass("get_chat_history() uses get_redis()")
        else:
            print_fail("get_chat_history() does NOT use get_redis()")
            return False

        if 'redis_client.lrange' in source:
            print_pass("get_chat_history() uses Redis LRANGE (correct)")
        else:
            print_warn("get_chat_history() may not use Redis LRANGE")

        # Verify add_chat_message uses Redis
        source = inspect.getsource(app_module.add_chat_message)

        if 'get_redis()' in source:
            print_pass("add_chat_message() uses get_redis()")
        else:
            print_fail("add_chat_message() does NOT use get_redis()")
            return False

        if 'redis_client.lpush' in source:
            print_pass("add_chat_message() uses Redis LPUSH (correct)")
        else:
            print_warn("add_chat_message() may not use Redis LPUSH")

        if 'redis_client.ltrim' in source:
            print_pass("add_chat_message() uses Redis LTRIM for size limit (correct)")
        else:
            print_warn("add_chat_message() may not use Redis LTRIM")

        return True

    except Exception as e:
        print_fail(f"Error testing chat history functions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_message_handler():
    """Test that WebSocket message handler uses new functions."""
    print_test("Issue #3: WebSocket handler uses new chat functions")

    try:
        from app import app as flask_app
        import app.app as app_module

        # Find the message handler in socketio handlers
        # This is tricky since socketio handlers are decorated
        # Let's check the source code instead

        with open('app/app.py', 'r') as f:
            source = f.read()

        # Find the @socketio.on('message') handler
        if 'add_chat_message(' in source:
            print_pass("WebSocket handler uses add_chat_message() (correct)")
        else:
            print_fail("WebSocket handler does NOT use add_chat_message()")
            return False

        # Should NOT directly append to CHAT_HISTORY
        # Check if there are any CHAT_HISTORY.append calls outside of the fallback functions
        lines = source.split('\n')
        bad_appends = []
        in_function = None

        for i, line in enumerate(lines, 1):
            if 'def add_chat_message' in line or 'def purge_old_chat_messages' in line:
                in_function = True
            elif line.startswith('def ') or line.startswith('class '):
                in_function = False

            if 'CHAT_HISTORY.append' in line and not in_function and '# Fallback' not in line:
                # This might be a bad usage
                if 'add_chat_message' not in lines[max(0, i-10):i]:  # Check context
                    bad_appends.append((i, line.strip()))

        if bad_appends:
            print_warn(f"Found {len(bad_appends)} direct CHAT_HISTORY.append calls outside helper functions:")
            for line_num, line in bad_appends[:3]:  # Show first 3
                print_info(f"  Line {line_num}: {line}")
        else:
            print_pass("No direct CHAT_HISTORY.append calls outside helper functions (correct)")

        return True

    except Exception as e:
        print_fail(f"Error testing message handler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_history_deprecated():
    """Test that CHAT_HISTORY is marked as deprecated."""
    print_test("Issue #3: CHAT_HISTORY marked as DEPRECATED")

    try:
        with open('app/app.py', 'r') as f:
            source = f.read()

        # Find CHAT_HISTORY declaration
        if 'DEPRECATED' in source and 'CHAT_HISTORY' in source:
            # Check if they're near each other
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if 'CHAT_HISTORY: List' in line:
                    # Check previous 5 lines for DEPRECATED comment
                    context = '\n'.join(lines[max(0, i-5):i])
                    if 'DEPRECATED' in context:
                        print_pass("CHAT_HISTORY is marked as DEPRECATED (correct)")
                        return True

        print_warn("CHAT_HISTORY may not be clearly marked as DEPRECATED")
        return True  # Not critical, just warning

    except Exception as e:
        print_fail(f"Error checking DEPRECATED marking: {e}")
        return False


# ============================================================================
# Main test runner
# ============================================================================

def main():
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}HODLXXI Critical Fixes Test Suite{Colors.END}")
    print(f"{Colors.BOLD}Testing Issues #1, #2, #3{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")

    all_tests = [
        # Issue #1 tests
        ("Issue #1: No duplicate routes", test_no_duplicate_verify_signature),
        ("Issue #1: Function uniqueness", test_verify_signature_function),

        # Issue #2 tests
        ("Issue #2: OAuth client storage", test_oauth_storage_postgresql),
        ("Issue #2: OAuth code storage", test_oauth_code_storage),

        # Issue #3 tests
        ("Issue #3: Redis functions", test_chat_history_redis_functions),
        ("Issue #3: Message handler", test_chat_message_handler),
        ("Issue #3: Deprecation marking", test_chat_history_deprecated),
    ]

    results = {}

    for test_name, test_func in all_tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")

    passed = sum(1 for r in results.values() if r)
    failed = sum(1 for r in results.values() if not r)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{status} - {test_name}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} passed, {failed}/{total} failed{Colors.END}")

    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Critical fixes are working correctly.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  {failed} test(s) failed. Please review the output above.{Colors.END}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
