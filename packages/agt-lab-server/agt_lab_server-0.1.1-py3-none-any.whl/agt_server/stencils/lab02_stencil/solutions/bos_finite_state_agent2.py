import sys
import os
# Add the core directory to the path (same approach as server.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.agents.common.base_agent import BaseAgent
from core.engine import Engine
from core.game.BOSGame import BOSGame
from core.agents.lab02.random_bos_agent import RandomBOSAgent


class BOSFiniteStateAgent2(BaseAgent):
    """Finite State Machine agent to counter the 'punitive' strategy."""
    
    def __init__(self, name: str = "BOSFSM2"):
        super().__init__(name)
        self.COMPROMISE, self.STUBBORN = 0, 1
        self.actions = [self.COMPROMISE, self.STUBBORN]
        self.curr_state = 0  # Initial state
        self.break_count = 0  # Track how many times we've broken compromise
    
    def get_action(self, obs):
        """
        Return either self.STUBBORN or self.COMPROMISE based on the current state.
        Strategy to counter "punitive":
        - The punitive agent goes to concert (STUBBORN) initially
        - Compromises once after opponent breaks compromise
        - Retaliates forever after 3 breaks
        - So we should be cooperative and avoid triggering retaliation
        """
        if self.curr_state == 0:
            # Initial state: start cooperative
            return self.COMPROMISE
        elif self.curr_state == 1:
            # Cooperative state: continue cooperating
            return self.COMPROMISE
        elif self.curr_state == 2:
            # Cautious state: be cooperative to avoid retaliation
            return self.COMPROMISE
        elif self.curr_state == 3:
            # Recovery state: try to rebuild cooperation
            return self.COMPROMISE
        else:
            return self.COMPROMISE  # Default fallback
    
    def update(self, reward: float, info=None, observation: dict = None, action: dict = None, done: bool = None):
        """
        Update the current state based on the game history.
        This should update self.curr_state based on your FSM transition rules.
        """
        self.reward_history.append(reward)
        
        # Get opponent's last action
        opponent_action = self.get_opponent_last_action()
        
        if opponent_action is not None:
            if opponent_action == self.COMPROMISE:
                # Opponent compromised
                if self.curr_state == 0:
                    # Initial state: opponent cooperated, stay cooperative
                    self.curr_state = 1
                elif self.curr_state == 1:
                    # Cooperative state: continue cooperating
                    pass
                elif self.curr_state == 2:
                    # Cautious state: opponent cooperated, back to cooperative
                    self.curr_state = 1
                elif self.curr_state == 3:
                    # Recovery state: opponent cooperated, back to cooperative
                    self.curr_state = 1
            else:
                # Opponent was stubborn
                if self.curr_state == 0:
                    # Initial state: opponent was stubborn, stay cooperative
                    self.curr_state = 1
                elif self.curr_state == 1:
                    # Cooperative state: opponent was stubborn, be cautious
                    self.curr_state = 2
                elif self.curr_state == 2:
                    # Cautious state: opponent was stubborn, try recovery
                    self.curr_state = 3
                elif self.curr_state == 3:
                    # Recovery state: opponent was stubborn, stay cautious
                    self.curr_state = 2
    
    def get_opponent_last_action(self):
        """Helper method to get opponent's last action (inferred from reward)."""
        if len(self.action_history) == 0:
            return None
        
        my_last_action = self.action_history[-1]
        my_last_reward = self.reward_history[-1]
        
        # Infer opponent's action from reward and my action
        if my_last_action == self.COMPROMISE:
            if my_last_reward == 0:
                return self.COMPROMISE  # Both compromised
            elif my_last_reward == 3:
                return self.STUBBORN     # I compromised, they were stubborn
        elif my_last_action == self.STUBBORN:
            if my_last_reward == 7:
                return self.COMPROMISE   # I was stubborn, they compromised
            elif my_last_reward == 0:
                return self.STUBBORN     # Both were stubborn
        
        return None  # Can't determine


# Agent name for submission
name = "BOSFiniteStateAgent2"


################### SUBMISSION #####################
agent_submission = BOSFiniteStateAgent2(name)
####################################################


if __name__ == "__main__":
    # Test your agent against the punitive strategy
    print("Testing BOS Finite State Agent 2...")
    print("=" * 50)
    
    # Import the punitive agent
    try:
        from bos_punitive import BOSPunitiveAgent
        opponent = BOSPunitiveAgent("Punitive")
    except ImportError:
        # Fallback to random agent if punitive agent doesn't exist
        opponent = RandomBOSAgent("Random")
        print("Note: Using Random agent as fallback (BOSPunitiveAgent not found)")
    
    # Create agents
    agent = BOSFiniteStateAgent2("Agent2")
    
    # Create game and run
    game = BOSGame(rounds=100)
    agents = [agent, opponent]
    
    engine = Engine(game, agents, rounds=100)
    final_rewards = engine.run()
    
    print(f"Final rewards: {final_rewards}")
    print(f"Cumulative rewards: {engine.cumulative_reward}")
    
    # Print statistics
    print(f"\n{agent.name} statistics:")
    action_counts = [0, 0]  # Compromise, Stubborn
    for action in agent.action_history:
        action_counts[action] += 1
    
    print(f"Compromise: {action_counts[0]}, Stubborn: {action_counts[1]}")
    print(f"Total reward: {sum(agent.reward_history)}")
    print(f"Average reward: {sum(agent.reward_history) / len(agent.reward_history) if agent.reward_history else 0:.3f}")
    print(f"Final state: {agent.curr_state}")
    
    print("\nTest completed!")
