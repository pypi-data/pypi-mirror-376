from auxiliary import llm_test, accepted_keys, safe_lambda
from src.fai.agent import ai_agent, simple_agent
from src.fai.agent import Agent

def sequential(agents: list[Agent], reducer, key: str = None):
    class Sequential(Agent):
        def __init__(self):
            super().__init__(key=key)
            self._agents = agents
            self._reducer = reducer

            if reducer is not None:
                self._reducer_keys = accepted_keys(self._reducer)

            assert len(self._agents) > 0, "Sequential operator requires at least one agent."

        def __call__(self, *args, **kwargs):
            results = {}

            for agent in self._agents:
                result = agent(*args, **kwargs)
                kwargs[agent.key] = agent(*args, **kwargs)
                results[agent.key] = result

            if reducer is not None:
                return safe_lambda(self._reducer, self._reducer_keys, **kwargs, **results)
            else:
                return None

        @property
        def key(self):
            return self._key \
                if self._key is not None \
                else self._agents[0].key

    return Sequential()

def test_sequential():
    def reducer(one, two, three):
        return f"Results: {one}, {two}, {three}"

    seq = sequential(agents=[
        simple_agent("One", key="one"),
        simple_agent("Two", key="two"),
        simple_agent("Three", key="three")
    ], reducer=reducer)

    print(seq())

def test_sequential_2():
    inf = ai_agent(lambda one, two: f"Combine these two stories: {one} and {two}")

    def reducer(one, two):
        return inf(one=one, two=two)

    seq = sequential(agents=[
        simple_agent("Cat", key="one"),
        simple_agent("Tree", key="two")], reducer=reducer)

    llm_test(seq)
