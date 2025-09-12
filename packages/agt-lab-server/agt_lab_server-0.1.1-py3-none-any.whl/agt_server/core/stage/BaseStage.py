from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Hashable, List, Tuple

PlayerId   = Hashable
ObsDict    = Dict[PlayerId, Any]
ActionDict = Dict[PlayerId, Any]
RewardDict = Dict[PlayerId, float]
InfoDict   = Dict[PlayerId, Dict[str, Any]]


class BaseStage(ABC):
    """
    All BaseStage subclasses MUST:
      - call BaseStage.__init__(num_players)
      - implement `legal_actions()`  (optional for offline stages)
      - implement `step()`, must set self._done = True when finished
    """

    def __init__(self, num_players: int):
        self.n = num_players
        self._done: bool = False


    def is_done(self) -> bool:
        """Return True once this Stage can no longer accept actions."""
        return self._done

    def _validate_actions(
        self, actions: ActionDict, expected_players: List[PlayerId] | None = None
    ) -> None:
        """
        Simple guard to keep Engine ⇄ Stage invariants honest.
        Raise ValueError if action_dict keys don't match the required movers.
        """
        print(f"[STAGE DEBUG] BaseStage._validate_actions called with actions: {actions}", flush=True)
        print(f"[STAGE DEBUG] Expected players: {expected_players}, self.n: {self.n}", flush=True)
        
        expected = set(expected_players) if expected_players is not None else set(range(self.n))
        print(f"[STAGE DEBUG] Expected player set: {expected}", flush=True)
        print(f"[STAGE DEBUG] Actual actions keys: {set(actions)}", flush=True)
        
        if set(actions) != expected:
            error_msg = f"Stage expected actions for players {sorted(expected)}, got {sorted(actions)}"
            print(f"[STAGE DEBUG] Validation failed: {error_msg}", flush=True)
            raise ValueError(error_msg)
        
        print(f"[STAGE DEBUG] Validation passed successfully", flush=True)



    @abstractmethod
    def legal_actions(self, player_id: PlayerId) -> Any:
        """
        Return a description of legal moves for `player_id`.
        Simultaneous games may ignore this (agents often know the domain).
        Sequential games & validators can use it for sanity checks.
        """

    @abstractmethod
    def step(
        self, actions: ActionDict
    ) -> Tuple[ObsDict, RewardDict, bool, InfoDict]:
        """
        Apply `actions`, update internal state, and return the usual gym-style tuple.
        Must set `self._done = True` when the Stage reaches a terminal state.
        """