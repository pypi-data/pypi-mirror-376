"""
Comprehensive simulation recorder for mesa-llm simulations.

This module provides tools to record all simulation events for post-analysis,
including agent observations, plans, actions, messages, and state changes.
"""

import json
import pickle
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class SimulationEvent:
    """A single recorded event in the simulation."""

    event_id: str
    timestamp: datetime
    step: int
    agent_id: int | None
    event_type: str
    content: dict[str, Any]
    metadata: dict[str, Any]


class SimulationRecorder:
    """
    Centralized recorder for capturing all simulation events for post-analysis.
    It captures agent observations, plans, actions, messages, state changes, etc.
    as well as model-level events and transitions.
    """

    def __init__(
        self,
        model,
        output_dir: str = "recordings",
        record_state_changes: bool = True,
        auto_save_interval: int | None = None,
    ):
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Recording configuration
        self.record_state_changes = record_state_changes
        self.auto_save_interval = auto_save_interval

        # Internal state
        self.events: list[SimulationEvent] = []
        self.simulation_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now(UTC)

        # Agent state tracking for change detection
        self.previous_agent_states: dict[int, dict[str, Any]] = {}

        # Auto-save counter
        self.events_since_save = 0

        # Initialize simulation metadata
        self.simulation_metadata = {
            "simulation_id": self.simulation_id,
            "start_time": self.start_time.isoformat(),
            "model_class": self.model.__class__.__name__,
        }

    def record_event(
        self,
        event_type: str,
        content: dict[str, Any] | str | None = None,
        agent_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        recipient_ids: list[int] | None = None,
    ):
        """Record a simulation event.

        Args:
            event_type: Type of event to record (observation, plan, action, message, state_change, etc.)
            content: Event content as dict or string
            agent_id: ID of the agent associated with this event
            metadata: Additional metadata for the event
            recipient_ids: List of recipient IDs for message events
        """

        # Handle different content formats based on event type
        if event_type == "message":
            if isinstance(content, str | dict | list):
                formatted_content = {
                    "message": content,
                    "recipient_ids": recipient_ids or [],
                }
            else:
                formatted_content = {
                    "message": content,
                    "recipient_ids": recipient_ids or [],
                }
        else:
            if isinstance(content, dict):
                formatted_content = content
            else:
                formatted_content = {"data": content}

        # Create the event
        event_id = f"{self.simulation_id}_{len(self.events):06d}"

        event = SimulationEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC),
            step=self.model.steps,
            agent_id=agent_id,
            event_type=event_type,
            content=formatted_content,
            metadata=metadata,
        )

        self.events.append(event)
        self.events_since_save += 1

        # Auto-save if configured
        if (
            self.auto_save_interval
            and self.events_since_save >= self.auto_save_interval
        ):
            filename = f"autosave_{self.simulation_id}_{len(self.events)}.json"
            self.save(filename)
            self.events_since_save = 0

    def record_model_event(self, event_type: str, content: dict[str, Any]):
        """Record a model-level event."""
        self.record_event(
            event_type=event_type,
            content=content,
            agent_id=None,
            metadata={"source": "model"},
        )

    def get_agent_events(self, agent_id: int) -> list[SimulationEvent]:
        """Get all events for a specific agent."""
        return [event for event in self.events if event.agent_id == agent_id]

    def get_events_by_type(self, event_type: str) -> list[SimulationEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]

    def get_events_by_step(self, step: int) -> list[SimulationEvent]:
        """Get all events from a specific simulation step."""
        return [event for event in self.events if event.step == step]

    def export_agent_memory(self, agent_id: int) -> dict[str, Any]:
        """Export agent memory state for external analysis."""
        agent_events = self.get_agent_events(agent_id)

        return {
            "agent_id": agent_id,
            "events": [asdict(event) for event in agent_events],
            "summary": {
                "total_events": len(agent_events),
                "event_types": list({event.event_type for event in agent_events}),
                "active_steps": list({event.step for event in agent_events}),
                "first_event": (
                    agent_events[0].timestamp.isoformat() if agent_events else None
                ),
                "last_event": (
                    agent_events[-1].timestamp.isoformat() if agent_events else None
                ),
            },
        }

    def save(self, filename: str | None = None, format: str = "json"):
        """Save complete simulation recording.

        Args:
            filename: Optional filename. If None, auto-generates based on format.
            format: Save format, either "json" or "pickle".
        """
        if format not in ["json", "pickle"]:
            raise ValueError("Format must be 'json' or 'pickle'")

        if filename is None:
            extension = "json" if format == "json" else "pkl"
            filename = f"simulation_{self.simulation_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.{extension}"

        filepath = self.output_dir / filename

        # Update metadata with final state
        self.simulation_metadata.update(
            {
                "end_time": datetime.now(UTC).isoformat(),
                "total_steps": self.model.steps,
                "total_events": len(self.events),
                "total_agents": len(self.model.agents),
                "duration_minutes": (
                    datetime.now(UTC) - self.start_time
                ).total_seconds()
                / 60,
                # Determine completion status gracefully when `max_steps` is absent
                "completion_status": (
                    "unknown"
                    if getattr(self.model, "max_steps", None) is None
                    else (
                        "interrupted"
                        if self.model.steps < self.model.max_steps
                        else "completed"
                    )
                ),
            }
        )

        # Record final model state
        self.record_model_event(
            event_type="simulation_end",
            content={
                "status": (
                    "unknown"
                    if getattr(self.model, "max_steps", None) is None
                    else (
                        "interrupted"
                        if self.model.steps < self.model.max_steps
                        else "completed"
                    )
                ),
                "final_step": self.model.steps,
                "total_events": len(self.events),
            },
        )

        # Prepare export data
        export_data = {
            "metadata": self.simulation_metadata,
            "events": [asdict(event) for event in self.events],
            "agent_summaries": {
                agent_id: self.export_agent_memory(agent_id)["summary"]
                for agent_id in {
                    event.agent_id
                    for event in self.events
                    if event.agent_id is not None
                }
            },
        }

        # Save based on format
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
        elif format == "pickle":
            with open(filepath, "wb") as f:
                pickle.dump(export_data, f)

        print(f"Simulation recording saved to: {filepath}")
        return filepath

    def get_stats(self) -> dict[str, Any]:
        """Get recording statistics."""
        agent_ids = {
            event.agent_id for event in self.events if event.agent_id is not None
        }

        return {
            "total_events": len(self.events),
            "unique_agents": len(agent_ids),
            "event_types": list({event.event_type for event in self.events}),
            "simulation_steps": self.model.steps,
            "recording_duration_minutes": (
                datetime.now(UTC) - self.start_time
            ).total_seconds()
            / 60,
            "events_per_agent": {
                agent_id: len(self.get_agent_events(agent_id)) for agent_id in agent_ids
            },
        }
