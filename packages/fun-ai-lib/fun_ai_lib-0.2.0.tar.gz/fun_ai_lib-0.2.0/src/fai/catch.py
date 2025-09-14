import time

from src.fai.agent import Agent, simple_agent

def catch(agent: Agent, exception: Agent):
    class Catch(Agent):
        def __init__(self, key: str = None):
            super().__init__(key)
            self._agent = agent
            self._exception = exception

        def __call__(self, *args, **kwargs):
            try:
                return self._agent(*args, **kwargs)
            except Exception as e:
                return exception(*args, **kwargs, error=e)

        @property
        def key(self):
            return self._key \
                if self._key is not None \
                else self._agent.key

    return Catch()

def retry(agent: Agent, key: str = None, timeout_millis: int = 1000, timeout_mult: int = 1, max_retry: int = 3):
    class Retry(Agent):
        def __init__(self):
            super().__init__(key)
            self._agent = agent
            self._timeout_millis = timeout_millis
            self._timeout_mult = timeout_mult
            self._max_retry = max_retry
            self._iteration = 0

        def __call__(self, *args, **kwargs):
            while True:
                try:
                    return agent(*args, **kwargs)
                except Exception as e:
                    timeout = self._timeout_millis * self._timeout_mult * self._iteration
                    seconds = timeout / 1000.0
                    time.sleep(seconds)

                    self._iteration += 1
                    if self._iteration > self._max_retry:
                        raise e

        @property
        def key(self):
            return self._key \
                if self._key is not None \
                else self._agent.key

    return Retry()

def test_catch():
    def agent_func():
        raise ValueError("An error occurred")

    def handle_func(error):
        return f"Handled error! {error}"

    result = catch(
        agent=simple_agent(call=agent_func),
        exception=simple_agent(call=handle_func))()

    assert "Handled error!" in result, "Catch should handle the error and return the handled value"
