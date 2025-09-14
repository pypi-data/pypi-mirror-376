from .cache import test_cache
from .catch import test_catch
from .extract import test_extract
from .agent import test_ai_agent, test_ai_agent_2
from .loop import test_loop
from .parallel import test_parallel, test_fork
from .sequential import test_sequential, test_sequential_2
from .switch import test_switch
from .transform import test_transform

def test_all():
    test_ai_agent()
    test_ai_agent_2()
    test_transform()
    test_cache()
    test_catch()
    test_extract()
    test_loop()
    test_switch()
    test_parallel()
    test_fork()
    test_sequential()
    test_sequential_2()

