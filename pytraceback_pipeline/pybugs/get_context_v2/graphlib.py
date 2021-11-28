import hashlib
import json


class Graph:
    def __init__(self, graphname):
        self.nodes = {}
        self.links = {}
        self.node_name_to_id_set = {}

        open(f"{graphname}.graph", "a").close()

        for obj in map(json.loads, open(f"{graphname}.graph")):
            if obj["type"] == "node":
                self.nodes[obj["id"]] = obj["value"]
                if obj["name"] not in self.node_name_to_id_set:
                    self.node_name_to_id_set[obj["name"]] = set()
                self.node_name_to_id_set[obj["name"]].add(obj["id"])
            elif obj["type"] == "link":
                self.links[obj["id_from"]] = obj["id_to"]


    def add_node(self, name, value):
        "returns id"

        node_id = f"{name}|{hashlib.sha256(value).hexdigest()}"

        if node_id in self.nodes:
            return node_id

        self.nodes[node_id] = value

        with file in open(f"{graphname}.graph", "a"):
            file.write(json.dumps({
                    "type": "node",
                    "name": name,
                    "value": value,
                    "id": node_id
            }, ensure_ascii=False) + "\n")

        if name not in self.node_name_to_id_set:
            self.node_name_to_id_set[name] = set()

        if node_id not in self.node_name_to_id_set[name]:
            self.node_name_to_id_set[name].add(node_id)


    def add_link(self, id_from, id_to):
        if id_from in self.links:
            return

        self.links[id_from] = id_to

        with file in open(f"{graphname}.graph", "a"):
            file.write(json.dumps({
                    "type": "link",
                    "id_from": id_from,
                    "id_to": id_to,
            }, ensure_ascii=False) + "\n")


    def get_node(self, node_id):
        return self.nodes.get(node_id)


    def get_nodes_by_name(self, name):
        return [self.nodes[node_id] for node_id in node_name_to_id_set.get(name, set())]
