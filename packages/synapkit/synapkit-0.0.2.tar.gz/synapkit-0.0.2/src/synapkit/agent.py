class Agent:
    """Minimal placeholder Agent for synapkit."""
    def init(self, name: str = "agent"):
        self.name = name

    def __repr__(self) -> str:
        return f"synapkit.Agent(name={self.name!r})" 
