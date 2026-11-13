#!/usr/bin/env python3
"""Benign local source fixtures for the route inventory helper."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("route_inventory.py")
SPEC = importlib.util.spec_from_file_location("route_inventory", SCRIPT)
route_inventory = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(route_inventory)


class RouteInventoryTests(unittest.TestCase):
    def test_lists_python_and_node_literal_routes_with_locations(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-") as td:
            root = Path(td)
            (root / "app.py").write_text(
                "@app.get('/health')\ndef health(): pass\n"
                "@router.route('/account', methods=['GET', 'POST'])\ndef account(): pass\n"
                "urlpatterns = [\n path('api/items/', view),\n]\n", encoding="utf-8")
            (root / "server.ts").write_text(
                "app.post('/api/login', handler);\n"
                "router.route('/api/data').get(handler);\n", encoding="utf-8")
            rows, skipped = route_inventory.inventory(root)
            self.assertEqual(skipped, 0)
            self.assertEqual([(r['method'], r['path_literal']) for r in rows], [
                ('GET', '/health'), ('GET,POST', '/account'), ('ROUTE', 'api/items/'),
                ('POST', '/api/login'), ('ROUTE', '/api/data'),
            ])
            self.assertTrue(all(r['file'] in {'app.py', 'server.ts'} and r['line'] > 0 for r in rows))

    def test_flask_route_default_is_get_and_runtime_auto_methods_are_not_asserted(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-flask-") as td:
            root = Path(td)
            (root / "app.py").write_text(
                "@app.route('/default')\ndef default(): pass\n"
                "@app.route('/post', methods=['POST'])\ndef post(): pass\n"
                "@app.route('/get-no-options', methods=['GET'], provide_automatic_options=False)\ndef get(): pass\n"
                "@app.route('/tuple', methods=('GET', 'OPTIONS'), provide_automatic_options=False)\ndef tuple_route(): pass\n"
                "@app.route('/dynamic', methods=METHODS)\ndef dynamic(): pass\n",
                encoding="utf-8",
            )
            rows, _ = route_inventory.inventory(root)
            by_path = {row["path_literal"]: row for row in rows}

            self.assertEqual(by_path["/default"]["method"], "GET")
            self.assertEqual(by_path["/default"]["method_source"], "flask-default")
            self.assertIsNone(by_path["/default"]["runtime_methods"])
            self.assertIn("may add HEAD", by_path["/default"]["runtime_method_note"])
            self.assertEqual(by_path["/post"]["method"], "POST")
            self.assertEqual(by_path["/post"]["method_source"], "explicit")
            self.assertIn("automatic OPTIONS depends", by_path["/post"]["runtime_method_note"])
            self.assertEqual(by_path["/get-no-options"]["method"], "GET")
            self.assertIn("explicitly disables automatic OPTIONS", by_path["/get-no-options"]["runtime_method_note"])
            self.assertEqual(by_path["/tuple"]["method"], "GET,OPTIONS")
            self.assertIn("OPTIONS is explicit", by_path["/tuple"]["runtime_method_note"])
            self.assertEqual(by_path["/dynamic"]["method"], "ROUTE")
            self.assertEqual(by_path["/dynamic"]["method_source"], "explicit-unknown")
            self.assertIn("not statically understood", by_path["/dynamic"]["runtime_method_note"])

    def test_flask_method_inference_does_not_guess_get_for_explicit_non_get_or_django(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-negative-") as td:
            root = Path(td)
            (root / "app.py").write_text(
                "@app.route('/only-delete', methods=['DELETE'])\ndef delete(): pass\n"
                "path('items/', view)\n",
                encoding="utf-8",
            )
            rows, _ = route_inventory.inventory(root)
            by_path = {row["path_literal"]: row for row in rows}

            self.assertEqual(by_path["/only-delete"]["method"], "DELETE")
            self.assertNotIn("GET", by_path["/only-delete"]["method"].split(","))
            self.assertEqual(by_path["items/"]["method"], "ROUTE")
            self.assertEqual(by_path["items/"]["method_source"], "static-declaration")
            self.assertIsNone(by_path["items/"]["runtime_methods"])

    def test_comments_vendor_build_and_oversize_files_are_excluded(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-") as td:
            root = Path(td)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "dep.js").write_text("app.get('/vendor', fn)")
            (root / "app.js").write_text(
                "// app.get('/comment', fn)\n"
                "/*\napp.get('/block-comment', fn)\n*/\n"
                "const note = 1; // app.get('/inline-comment', fn)\n"
                "app.get('/real', fn)\n"
            )
            (root / "large.py").write_text("x" * 300)
            rows, skipped = route_inventory.inventory(root, max_file_bytes=200)
            self.assertEqual([r['path_literal'] for r in rows], ['/real'])
            self.assertEqual(skipped, 1)

    def test_dynamic_and_malformed_sources_do_not_create_guessed_routes(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-") as td:
            root = Path(td)
            (root / "app.js").write_text("app.get('/users/' + id, fn)\nrouter.post(pathVar, fn)\n")
            rows, _ = route_inventory.inventory(root)
            self.assertEqual(rows, [])

    def test_symlinked_source_outside_root_is_not_read(self):
        with tempfile.TemporaryDirectory(prefix="route-inventory-") as td, tempfile.TemporaryDirectory(prefix="route-canary-") as outside_td:
            root = Path(td)
            outside = Path(outside_td) / "outside.py"
            outside.write_text("@app.get('/outside-secret')\ndef x(): pass\n", encoding="utf-8")
            (root / "linked.py").symlink_to(outside)
            rows, _ = route_inventory.inventory(root)
            self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
