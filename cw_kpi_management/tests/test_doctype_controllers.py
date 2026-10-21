# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Every DocType's controller defines the class Frappe imports: the name without spaces.

A wrong class name only fails on the site, during migrate ("ImportError: <DocType>"),
so it is checked here, without a bench.
"""

import json
import pathlib
import re
import unittest

APP = pathlib.Path(__file__).resolve().parents[1]


class ControllerClassNames(unittest.TestCase):
	def test_class_matches_doctype(self):
		checked = 0
		for meta in APP.glob("*/doctype/*/*.json"):
			if meta.stem != meta.parent.name:
				continue
			doc = json.loads(meta.read_text(encoding="utf-8"))
			if doc.get("doctype") != "DocType":
				continue
			controller = meta.with_suffix(".py")
			self.assertTrue(controller.exists(), f"{doc['name']}: no controller {controller.name}")
			expected = doc["name"].replace(" ", "").replace("-", "")
			classes = re.findall(r"^class (\w+)\(", controller.read_text(encoding="utf-8"), re.M)
			self.assertIn(expected, classes, f"{doc['name']}: expected class {expected}, found {classes}")
			checked += 1
		self.assertGreater(checked, 5)


if __name__ == "__main__":
	unittest.main()
