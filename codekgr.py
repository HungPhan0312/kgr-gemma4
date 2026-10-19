import ast, difflib, json, math, os, random, re, subprocess, time
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd

CFG = dict(
    seed=42,
    dataset="princeton-nlp/SWE-bench_Lite",
    split="test",
    repo_filter=None,
    n_issues=40,
    time_budget_hours=9.5,
    workdir="/kaggle/working/codekgr" if Path("/kaggle").exists() else "./codekgr_work",
    top_k=10,
    context_char_budget=24000,
    critic_rounds=2,
    verifier_rounds=2,
    max_new_tokens=1024,
    temperature=0.0,
    architectures=["A1", "A2", "A3", "A4", "A5", "A6", "A7"],
    model_name="gemma-4-codekgr",
)

MOCK_CODEBASE = """
class DataPipeline:
    def __init__(self, raw_records):
        self.raw_records = raw_records
        self.cleaned_data = []

    def sanitize_record(self, record):
        return self._normalize_types(record)

    def _normalize_types(self, item):
        return item['val']

    def calculate_total_volume(self):
        total = 0.0
        for r in self.raw_records:
            total += self.sanitize_record(r)
        return total

    def export_summary(self):
        pass

    def audit_trail_generator(self):
        pass
"""

UNIT_TEST_CODE = """
def test_pipeline_heterogeneous_input():
    raw_data = [{'val': 10.5}, {'val': "20.5"}, {'val': 30.0}]
    pipeline = DataPipeline(raw_data)
    result = pipeline.calculate_total_volume()
    assert result == 61.0, f"Expected 61.0, but got {result}"
"""

class DependencyPruner(ast.NodeVisitor):
    def __init__(self, target_func_name):
        self.target = target_func_name
        self.call_graph = {}
        self.current_func = None
        self.func_nodes = {}

    def visit_FunctionDef(self, node):
        prev_func = self.current_func
        self.current_func = node.name
        self.func_nodes[node.name] = node
