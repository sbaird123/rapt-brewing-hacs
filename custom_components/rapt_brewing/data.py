"""Data classes for RAPT Brewing integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .const import (
    FERMENTATION_STAGE_PRIMARY,
    SESSION_STATE_IDLE,
)


@dataclass
class BrewingSession:
    """Represent a brewing session."""
    
    id: str
    name: str
    recipe: str | None = None
    original_gravity: float | None = None
    target_gravity: float | None = None
    target_temperature: float | None = None
    current_gravity: float | None = None
    current_temperature: float | None = None
    alcohol_percentage: float | None = None
    attenuation: float | None = None
    fermentation_rate: float | None = None
    state: str = SESSION_STATE_IDLE
    stage: str = FERMENTATION_STAGE_PRIMARY
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    data_points: list[DataPoint] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "recipe": self.recipe,
            "original_gravity": self.original_gravity,
            "target_gravity": self.target_gravity,
            "target_temperature": self.target_temperature,
            "current_gravity": self.current_gravity,
            "current_temperature": self.current_temperature,
            "alcohol_percentage": self.alcohol_percentage,
            "attenuation": self.attenuation,
            "fermentation_rate": self.fermentation_rate,
            "state": self.state,
            "stage": self.stage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "alerts": [alert.to_dict() for alert in self.alerts],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrewingSession:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            recipe=data.get("recipe"),
            original_gravity=data.get("original_gravity"),
            target_gravity=data.get("target_gravity"),
            target_temperature=data.get("target_temperature"),
            current_gravity=data.get("current_gravity"),
            current_temperature=data.get("current_temperature"),
            alcohol_percentage=data.get("alcohol_percentage"),
            attenuation=data.get("attenuation"),
            fermentation_rate=data.get("fermentation_rate"),
            state=data.get("state", SESSION_STATE_IDLE),
            stage=data.get("stage", FERMENTATION_STAGE_PRIMARY),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            notes=data.get("notes"),
            data_points=[DataPoint.from_dict(dp) for dp in data.get("data_points", [])],
            alerts=[Alert.from_dict(alert) for alert in data.get("alerts", [])],
        )


@dataclass
class DataPoint:
    """Represent a data point in a brewing session."""
    
    timestamp: datetime
    gravity: float | None = None
    temperature: float | None = None
    battery_level: int | None = None
    signal_strength: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "gravity": self.gravity,
            "temperature": self.temperature,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataPoint:
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            gravity=data.get("gravity"),
            temperature=data.get("temperature"),
            battery_level=data.get("battery_level"),
            signal_strength=data.get("signal_strength"),
        )


@dataclass
class Alert:
    """Represent an alert in a brewing session."""
    
    type: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alert:
        """Create from dictionary."""
        return cls(
            type=data["type"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            acknowledged=data.get("acknowledged", False),
        )


@dataclass
class RAPTBrewingData:
    """Runtime data for RAPT Brewing integration."""
    
    sessions: dict[str, BrewingSession] = field(default_factory=dict)
    current_session: BrewingSession | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    
    def add_session(self, session: BrewingSession) -> None:
        """Add a brewing session."""
        self.sessions[session.id] = session
    
    def get_session(self, session_id: str) -> BrewingSession | None:
        """Get a brewing session by ID."""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> None:
        """Remove a brewing session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def set_current_session(self, session_id: str | None) -> None:
        """Set the current active session."""
        if session_id is None:
            self.current_session = None
        else:
            self.current_session = self.sessions.get(session_id)