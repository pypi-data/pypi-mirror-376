from concurrent.futures import ThreadPoolExecutor

from auxiliary import safe_lambda, accepted_keys
from src.fai.agent import ai_agent
from src.fai.agent import Agent, simple_agent

def parallel(agents: list[Agent], reducer, key: str = None):
    class Parallel(Agent):
        def __init__(self):
            super().__init__(key=key)
            self.agents = agents
            self.reducer = reducer

            assert len(self.agents) != 0, "Agents list cannot be empty"

            if reducer is not None:
                self.reducer_keys = accepted_keys(self.reducer)

        def __call__(self, *args, **kwargs):
            with ThreadPoolExecutor() as executor:
                results = [executor.submit(agent, *args, **kwargs) for agent in agents]
                results = [f.result() for f in results]
                results = {agent.key: result for agent, result in zip(self.agents, results)}

            if reducer is not None:
                return safe_lambda(self.reducer, self.reducer_keys, **kwargs, **results)
            else:
                return None

        @property
        def key(self):
            return self._key \
                if self._key is not None \
                else self.agents[0].key

    return Parallel()

def ai_parallel(template, agents: list[Agent], llm: str = None, tools: list = None, key: str = None):
    def reducer(**kwargs):
        return ai_agent(template, llm, tools)(**kwargs)
    return parallel(agents, reducer, key)

def fork(agent: Agent, mapper, reducer, key: str = None) -> Agent:
    class Fork(Agent):
        def __init__(self):
            super().__init__(key=key)
            self._agent = agent
            self._mapper = mapper
            self._reducer = reducer

        def __call__(self, *args, **kwargs):
            result = {self._agent.key: self._agent(*args, **kwargs)}
            agents = mapper(**result)

            with ThreadPoolExecutor() as executor:
                results = [executor.submit(trg, *args, **kwargs) for trg in agents]
                results = [f.result() for f in results]

            return self._reducer(results)

        @property
        def key(self):
            return self._key \
                if self._key is not None \
                else self._agent.key

    return Fork()

def test_parallel():
    def reducer(one, two, three):
        return f"{one}: One | {two}: Two | {three}: Three"

    join_agent = parallel(
        agents=[
            simple_agent(call="One", key="one"),
            simple_agent(call="Two", key="two"),
            simple_agent(call="Tree", key="three")
        ],
        reducer=reducer
    )

    result = join_agent()
    assert result == "One: One | Two: Two | Tree: Three", \
        f"Expected 'One: One | Two: Two | Tree: Three', got {result}"
    
def test_fork():
    def example_mapper(dum):
        return [simple_agent(f"Mapped 1: {dum}"),
                simple_agent(f"Mapped 2: {dum}")]

    def example_reducer(mapped_results):
        return " | ".join(mapped_results)

    forked_agent = fork(
        agent=simple_agent("Hello, World!", key="dum"),
        mapper=example_mapper,
        reducer=example_reducer,
        key="forked_example"
    )

    assert forked_agent() == "Mapped 1: Hello, World! | Mapped 2: Hello, World!"
