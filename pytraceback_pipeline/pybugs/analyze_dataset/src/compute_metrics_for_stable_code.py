#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import numpy as np
from radon.visitors import ComplexityVisitor
from radon.complexity import cc_rank
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze
import re


DATA_DIR = os.getenv("HOME") + '/zephyr_data/stable_code/'


def removeExtraSpaces(snippet):
    number_of_spaces_to_remove = re.search('\S', snippet.split('\n')[0]).start(0)
    return '\n'.join([snippet_line[number_of_spaces_to_remove:]
                      for snippet_line in snippet.split('\n')])


def refineSnippet(snippet):
    try:
        ComplexityVisitor.from_code(snippet)
        return snippet
    except:
        try:
            snippet_with_removed_extra_spaces = removeExtraSpaces(snippet)
            ComplexityVisitor.from_code(snippet_with_removed_extra_spaces)
            return snippet_with_removed_extra_spaces
        except:
            return np.nan


def computeCyclomaticComplexity(snippet):
    try:
        return ComplexityVisitor.from_code(snippet).functions_complexity
    except SyntaxError:
        return None


def isFunction(snippet):
    return not ComplexityVisitor.from_code(snippet).functions[0].is_method


def computeHastadMetrics(snippet):
    try:
        hastad_metrics = h_visit(snippet).total
        return {metric:getattr(hastad_metrics, metric) for metric in dir(hastad_metrics)
                if (not metric.startswith('_')) and ('index' not in metric) and ('count' not in metric)}
    except SyntaxError:
        return None


def computeRawMetrics(snippet):
    try:
        raw_metrics = analyze(snippet)
        return {metric:getattr(raw_metrics, metric) for metric in dir(raw_metrics)
                if (not metric.startswith('_')) and ('index' not in metric) and ('count' not in metric)}
    except SyntaxError:
        return None


def computeMIindex(snippet):
    try:
        return mi_visit(snippet, multi=False)
    except SyntaxError:
        return None


chunk_size = 500000
i = 0

for data in pd.read_csv(DATA_DIR + 'top_proj_code_samples_v4.csv',
                        chunksize=chunk_size):
    if i < 8:
        i += 1
        continue

    print(f"Processing {i+1}th chunk")
    data['before_merge'] = data['before_merge'].apply(refineSnippet)
    data = data.loc[data['before_merge'].notna()]

    data['cc_before'] = data['before_merge'].apply(computeCyclomaticComplexity)
    data['is function_before'] = data['before_merge'].apply(isFunction)
    data['cc_rank_before'] = data['cc_before'].apply(cc_rank)

    hastad_metrics_before = data['before_merge'].apply(computeHastadMetrics)
    for col in hastad_metrics_before.iloc[-1].keys():
        data[col + '_before'] = hastad_metrics_before.apply(lambda x: x[col] if x else np.nan)

    raw_metrics_before = data['before_merge'].apply(computeRawMetrics)
    for col in raw_metrics_before.iloc[-1].keys():
        data[col + '_before'] = raw_metrics_before.apply(lambda x: x[col] if x else np.nan)

    data['MI_before'] = data['before_merge'].apply(computeMIindex)

    data.to_pickle(DATA_DIR + 'stable_code_' + str(i) + '.pickle')
    print(f"Processed chunk {i+1}") 
    i += 1

