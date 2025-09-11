from pathlib import Path
from collections import defaultdict
import os
import json

class GraphPipeline:
    def __init__(self, root_folder: str):
        self.root_folder = Path(root_folder)

        self.graph = defaultdict(list)
        self.nodes = {}

    def add_node(self, cls, dependencies=None):
        name = cls.__class__.__name__
        identity = hex(id(cls))
        self.nodes[identity] = cls
        if dependencies:
            for dep in dependencies:
                dependent_identity = hex(id(dep))
                dep_name = dependent_identity if isinstance(dep, type) else dep
                self.graph[dep_name].append(name)
        else:
            self.graph[identity] = self.graph.get(identity, [])

    def execute(self):

        pdf_files =  list(self.root_folder.rglob("*.pdf"))

        for pdf_file in pdf_files:
            for name, step in self.nodes.items():
                if name in self.graph.keys():
                    hash_ = self.compute_hash(step)
                    path = Path(pdf_file.parent / hash_)
                    path.mkdir(parents=True, exist_ok=True)
                    file_path = path / Path(pdf_file.name).with_suffix(".md")
                    if file_path.exists():
                        result = file_path.read_text(encoding="utf-8")
                    else:
                        result = step(pdf_file)
                        file_path.write_text(result, encoding="utf-8")
                        json_parameter = file_path.parent / "paramter.json"
                        attrs = {k: v for k, v in step.__dict__.items() if not k.startswith('_')}
                        json_parameter.write_text(json.dumps(attrs), encoding="utf-8")
                else:
                    result = file_path.read_text(encoding="utf-8")
                    result = step(result)
                    print(result)


                #outputs = self._process_single_pdf(pdf_path, max_cycles)

                #output_file = self.output_folder / f"{subfolder.name}.json"
                #with open(output_file, "w", encoding="utf-8") as f:
                #    json.dump(outputs, f, indent=2)

    @staticmethod
    def compute_hash(cls) -> str:
        import hashlib
        # Collect all instance attributes
        attrs = {k: v for k, v in cls.__dict__.items() if k != "hash"}
        # Convert to JSON string for a stable representation
        attrs_str = json.dumps(attrs, sort_keys=True, default=str)
        # Return SHA256 hash
        return hashlib.sha256(attrs_str.encode()).hexdigest()