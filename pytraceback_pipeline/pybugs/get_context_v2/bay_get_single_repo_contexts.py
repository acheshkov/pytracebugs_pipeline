import pickle
import json
import hashlib
import os
import copy
import collections

from tree_sitter import Language, Parser
from process import DataProcessor
from parsers.python_parser import PythonParser

def savable_cache(f):
    filename = f.__name__.replace("/", "_").replace(".", "_") + ".cache"

    open(filename, "a").close()
    cache = {obj["key"]: obj["value"] for obj in map(json.loads, open(filename, "r"))}

    def new_f(*args):
        key = hashlib.sha256(json.dumps(args, ensure_ascii=False).encode()).hexdigest()
        if key not in cache:
            cache[key] = f(*args)

            with open(filename, "a") as file:
                print({"key": key, "value": cache[key]})
                file.write(json.dumps({"key": key, "value": cache[key]}, ensure_ascii=False) + "\n")
        return cache[key]
    return new_f


def make_processor():
    DataProcessor.PARSER.set_language(Language('/home5/u1333/zephyr_contexts/py-tree-sitter-languages.so', 'python'))
    processor = DataProcessor(language="python", language_parser=PythonParser)
    return processor

@savable_cache
def process_definitions(name, directory):
    processor = make_processor()
    return processor.process_definitions(name, directory, ext="py")


@savable_cache
def process_calls(name, directory, definitions):
    processor = make_processor()
    return processor.process_calls(name, directory, ext="py", library_candidates=definitions)


def get_flat_definitions_with_calls(definitions, calls):
    calls_by_nwo_path = collections.defaultdict(list)
    inv_calls_by_nwo_path = collections.defaultdict(list)

    for call in calls:
        call_nwo_path = (call["call_nwo"], call["call_path"])
        calling_nwo_path = (call["calling_nwo"], call["calling_path"])

        calls_by_nwo_path[call_nwo_path].append(call)
        inv_calls_by_nwo_path[calling_nwo_path].append(call)


    flat_definitions = {}

    for module in definitions:
        for definition in definitions[module]:
            nwo_path_identifier = (definition["nwo"], definition["path"], definition["identifier"])
            nwo_path = (definition["nwo"], definition["path"])

            flat_definitions[nwo_path_identifier] = copy.deepcopy(definition)

            for call in calls_by_nwo_path[nwo_path]:
                if call["called_identifier"] == definition["identifier"]:
                    flat_definitions[nwo_path_identifier]["called"].append(call)

            for call in inv_calls_by_nwo_path[nwo_path]:
                if (definition["start_point"][0] <= call["calling_start_point"][0] <= definition["end_point"][0] and
                    definition["start_point"][0] <= call["calling_end_point"][0] <= definition["end_point"][0]):
                    flat_definitions[nwo_path_identifier]["calls"].append(call)

    return flat_definitions

# {'nwo': 'numpy/numpy', 'sha': 'e5f6012b9d59848d1b76e1b09982cbc67989572b', 'path': 'numpy_numpy/pavement.py', 'identifier': 'tarball_name', 'function': 'def tarball_name(ftype=\'gztar\'):\n    """Generate source distribution name\n\n    Parameters\n    ----------\n    ftype : {\'zip\', \'gztar\'}\n        Type of archive, default is \'gztar\'.\n\n    """\n    root = f\'numpy-{FULLVERSION}\'\n    if ftype == \'gztar\':\n        return root + \'.tar.gz\'\n    elif ftype == \'zip\':\n        return root + \'.zip\'\n    raise ValueError(f"Unknown type {type}")', 'start_point': [66, 0], 'end_point': [80, 44], 'called': [], 'calls': []}

# {'calling_nwo': 'numpy/numpy', 'calling_sha': 'e5f6012b9d59848d1b76e1b09982cbc67989572b', 'calling_path': 'numpy_numpy/doc/cdoc/numpyfilter.py', 'called_identifier': 'filter_comment', 'called_library_name': 'numpy', 'calling_start_point': [55, 15], 'calling_end_point': [55, 29], 'call_nwo': 'numpy/numpy', 'call_path': 'numpy_numpy/doc/cdoc/numpyfilter.py', 'call_start_point': [36, 0], 'call_end_point': [43, 15]}


NWO = "numpy/numpy"
# NWO = "bay/bay_module"
NWO_TO_DIR = {
    "numpy/numpy": "numpy_numpy",
    "bay/bay_module": "bay_module"
}


def get_called_func_contents(directory, lib_name, filepath, start_point, end_point):
    if not dir:
        return

    with open(os.path.join(directory, lib_name, filepath.lstrip("/"))) as f:
        lines = f.readlines()

    return lines[start_point:end_point]


definitions = {}
definitions['numpy'] = process_definitions(NWO, NWO_TO_DIR[NWO])
# definitions['b'] = process_definitions(NWO, NWO_TO_DIR[NWO])

# print(definitions)

# print(definitions['numpy/numpy'])

calls = []
calls += process_calls(NWO, NWO_TO_DIR[NWO], definitions)
# print("calls", calls)

# print(calls)

# calls_graph = graphlib.Graph("calls")
# inv_calls_graph = graphlib.Graph("inv_calls")

flat_definitions = get_flat_definitions_with_calls(definitions, calls)

AUGMENTED_DIR_NAME = "augmented"
try:
    os.mkdir(AUGMENTED_DIR_NAME)
except FileExistsError:
    pass

flat_definitions_by_path = collections.defaultdict(list)

for nwo, path, identifier in flat_definitions:
    flat_definitions_by_path[path].append([identifier, flat_definitions[nwo, path, identifier]])
    # print(nwo, path, identifier)

def write_augmented_file(file, path, flat_definitions_by_path, level=0, max_level=1, start_line=0, end_line=None):
    if level > max_level:
        return

    line_to_calls = collections.defaultdict(list)

    for identifier, definition in flat_definitions_by_path[path]:
        # print(definition)
        for call in definition["calls"]:
            line_to_calls[call["calling_start_point"][0]].append(call)

    file_lines = open(path).readlines()

    for pos, line in enumerate(file_lines):
        if pos < start_line:
            continue
        if end_line is not None and pos > end_line:
            break

        SPACES_PER_LEVEL=4
        file.write("." *(level * SPACES_PER_LEVEL) + line)

        for call in line_to_calls[pos]:
            write_augmented_file(file, call["call_path"], flat_definitions_by_path, level+1, max_level,
                                 call["call_start_point"][0], call["call_end_point"][0])
            # call_lines = open()
            # print(call)


for path in flat_definitions_by_path:
    print(path)
    file = open(AUGMENTED_DIR_NAME + "/" + path.replace("/", "_"), "w")

    write_augmented_file(file, path, flat_definitions_by_path, max_level=4)

