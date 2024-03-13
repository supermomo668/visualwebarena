class Registry:
    def __init__(self):
        self._registry = {}

    def register(self, name, cls):
        self._registry[name] = cls

    def get(self, name):
        cls = self._registry.get(name)
        if not cls:
            raise ValueError(f"Pipeline {name} not found")
        return cls()
    
    def __call__(self, name):
        # Correct way to return a registered function by name
        if name in self:
            return self[name]
        else:
            raise KeyError(f"No evaluator registered under the name '{name}'.")

pipeline_registry = Registry()d


class EvaluatorRegistry(dict):
    def __init__(self, name=None, default_ontology=None):
        super().__init__()
        self.name = name
        self.default_ontology = default_ontology
        
    def register(self, name, ontology=None):
        # Use default ontology if none specified
        if ontology is None:
            ontology = self.default_ontology
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Wrap inputs in AgentAction objects (text input only)
                wrapped_args = [
                  ontology(arg) if isinstance(arg, str) else arg for arg in args
                ]
                # Call the original function with wrapped inputs
                return func(*wrapped_args, **kwargs)
            self[name] = wrapper
            return wrapper
        return decoratord