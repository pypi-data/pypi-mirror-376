# tests/test_llm_agent.py

import re

from mesa.model import Model
from mesa.space import MultiGrid

from mesa_llm import Plan
from mesa_llm.llm_agent import LLMAgent
from mesa_llm.memory.st_memory import ShortTermMemory
from mesa_llm.reasoning.react import ReActReasoning


def test_apply_plan_adds_to_memory(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")

    class DummyModel(Model):
        def __init__(self):
            super().__init__(seed=42)
            self.grid = MultiGrid(3, 3, torus=False)

        def add_agent(self, pos):
            system_prompt = "You are an agent in a simulation."
            agents = LLMAgent.create_agents(
                self,
                n=1,
                reasoning=ReActReasoning,
                system_prompt=system_prompt,
                vision=-1,
                internal_state=["test_state"],
            )

            x, y = pos

            self.grid.place_agent(agents[0], (x, y))
            return agents[0]

    model = DummyModel()
    agent = model.add_agent((1, 1))
    agent.memory = ShortTermMemory(
        agent=agent,
        n=5,
        display=True,
    )

    # fake response returned by the tool manager
    fake_response = [{"tool": "foo", "argument": "bar"}]

    # monkeypatch the tool manager so no real tool calls are made
    monkeypatch.setattr(
        agent.tool_manager, "call_tools", lambda agent, llm_response: fake_response
    )

    plan = Plan(step=0, llm_plan="do something")

    resp = agent.apply_plan(plan)

    assert resp == fake_response

    assert {
        "tool": "foo",
        "argument": "bar",
    } in agent.memory.step_content.values() or agent.memory.step_content == {
        "tool": "foo",
        "argument": "bar",
    }


def test_generate_obs_with_one_neighbor(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")

    class DummyModel(Model):
        def __init__(self):
            super().__init__(seed=45)
            self.grid = MultiGrid(3, 3, torus=False)

        def add_agent(self, pos, agent_class=LLMAgent):
            system_prompt = "You are an agent in a simulation."
            agents = agent_class.create_agents(
                self,
                n=1,
                reasoning=ReActReasoning,
                system_prompt=system_prompt,
                vision=-1,
                internal_state=["test_state"],
            )
            x, y = pos
            self.grid.place_agent(agents[0], (x, y))
            return agents[0]

    model = DummyModel()

    agent = model.add_agent((1, 1))
    agent.memory = ShortTermMemory(
        agent=agent,
        n=5,
        display=True,
    )
    agent.unique_id = 1

    neighbor = model.add_agent((1, 2))
    neighbor.memory = ShortTermMemory(
        agent=agent,
        n=5,
        display=True,
    )
    neighbor.unique_id = 2
    monkeypatch.setattr(agent.memory, "add_to_memory", lambda *args, **kwargs: None)

    obs = agent.generate_obs()

    assert obs.self_state["agent_unique_id"] == 1

    # we should have exactly one neighboring agent in local_state
    assert len(obs.local_state) == 1

    # extract the neighbor
    key = next(iter(obs.local_state.keys()))
    assert key == "LLMAgent 2"

    entry = obs.local_state[key]
    assert entry["position"] == (1, 2)
    assert entry["internal_state"] == ["test_state"]


def test_send_message_updates_both_agents_memory(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")

    class DummyModel(Model):
        def __init__(self):
            super().__init__(seed=45)
            self.grid = MultiGrid(3, 3, torus=False)

        def add_agent(self, pos, agent_class=LLMAgent):
            system_prompt = "You are an agent in a simulation."
            agents = agent_class.create_agents(
                self,
                n=1,
                reasoning=lambda agent: None,
                system_prompt=system_prompt,
                vision=-1,
                internal_state=["test_state"],
            )
            x, y = pos
            self.grid.place_agent(agents[0], (x, y))
            return agents[0]

    model = DummyModel()
    sender = model.add_agent((0, 0))
    sender.memory = ShortTermMemory(
        agent=sender,
        n=5,
        display=True,
    )
    sender.unique_id = 1

    recipient = model.add_agent((1, 1))
    recipient.memory = ShortTermMemory(
        agent=recipient,
        n=5,
        display=True,
    )
    recipient.unique_id = 2

    # Track how many times add_to_memory is called
    call_counter = {"count": 0}

    def fake_add_to_memory(*args, **kwargs):
        call_counter["count"] += 1

    # monkeypatch both agents' memory modules
    monkeypatch.setattr(sender.memory, "add_to_memory", fake_add_to_memory)
    monkeypatch.setattr(recipient.memory, "add_to_memory", fake_add_to_memory)

    result = sender.send_message("hello", recipients=[recipient])
    pattern = r"LLMAgent 1 → \[<mesa_llm\.llm_agent\.LLMAgent object at 0x[0-9A-Fa-f]+>\] : hello"
    assert re.match(pattern, result)

    # sender + recipient memory => should be called twice
    assert call_counter["count"] == 2
