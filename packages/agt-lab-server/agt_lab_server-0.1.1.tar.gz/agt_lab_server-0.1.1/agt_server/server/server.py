#!/usr/bin/env python3
"""
Modern AGT Server for Lab Competitions

This server allows students to connect their completed stencils and compete against each other
in all the labs we've implemented: RPS, BOS, Chicken, Lemonade, and Auctions.
"""

import asyncio
import json
import socket
import time
import argparse
import os
import sys
import logging
import signal
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np

# Dashboard is now separate - no longer integrated

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game.RPSGame import RPSGame
from core.game.BOSGame import BOSGame
from core.game.BOSIIGame import BOSIIGame
from core.game.ChickenGame import ChickenGame
from core.game.PDGame import PDGame
from core.game.LemonadeGame import LemonadeGame
from core.game.AuctionGame import AuctionGame
from core.game.AdxTwoDayGame import AdxTwoDayGame
from core.game.AdxOneDayGame import AdxOneDayGame


@dataclass
class PlayerConnection:
    """Represents a connected player."""
    name: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    address: Tuple[str, int]
    device_id: str
    connected_at: float
    game_history: List[Dict[str, Any]]
    current_game: Optional[str] = None
    read_lock: Optional[asyncio.Lock] = None
    pending_action: Optional[Any] = None
    total_reward: float = 0.0
    games_played: int = 0
    
    def __post_init__(self):
        if self.read_lock is None:
            self.read_lock = asyncio.Lock()


class AGTServer:
    """Modern AGT Server for lab competitions."""
    
    def __init__(self, config: Dict[str, Any], host: str = "0.0.0.0", port: int = 8080, verbose: bool = False):
        self.config = config
        self.host = host
        self.port = port
        self.verbose = verbose
        
        # Server state
        self.players: Dict[str, PlayerConnection] = {}
        self.games: Dict[str, Any] = {}
        self.results: List[Dict[str, Any]] = []
        
        # Game restrictions
        self.allowed_games = config.get("allowed_games", None)  # none means all games allowed
        
        # Setup logging - minimal output
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create results directory
        os.makedirs("results", exist_ok=True)
        
        # Game configurations
        self.game_configs = {
            "rps": {
                "name": "Rock Paper Scissors",
                "game_class": RPSGame,
                "num_players": 2,
                "num_rounds": 100,
                "description": "Classic Rock Paper Scissors game"
            },
            "bos": {
                "name": "Battle of the Sexes",
                "game_class": BOSGame,
                "num_players": 2,
                "num_rounds": 100,
                "description": "Battle of the Sexes coordination game"
            },
            "bosii": {
                "name": "Battle of the Sexes II",
                "game_class": BOSIIGame,
                "num_players": 2,
                "num_rounds": 100,
                "description": "Battle of the Sexes with incomplete information"
            },
            "chicken": {
                "name": "Chicken Game",
                "game_class": ChickenGame,
                "num_players": 2,
                "num_rounds": 100,
                "description": "Chicken game with Q-Learning and collusion"
            },
            "pd": {
                "name": "Prisoner's Dilemma",
                "game_class": PDGame,
                "num_players": 2,
                "num_rounds": 100,
                "description": "Classic Prisoner's Dilemma game"
            },
            "lemonade": {
                "name": "Lemonade Stand",
                "game_class": LemonadeGame,
                "num_players": 3,
                "num_rounds": 100,
                "description": "3-player Lemonade Stand positioning game"
            },
            "auction": {
                "name": "Simultaneous Auction",
                "game_class": AuctionGame,
                "num_players": 2,
                "num_rounds": 10,
                "description": "Simultaneous sealed bid auction"
            },
            "adx_twoday": {
                "name": "Ad Exchange (Two Day)",
                "game_class": AdxTwoDayGame,
                "num_players": 2,
                "num_rounds": 2,
                "description": "Two-day ad exchange game"
            },
            "adx_oneday": {
                "name": "Ad Exchange (One Day)",
                "game_class": AdxOneDayGame,
                "num_players": 2,
                "num_rounds": 1,
                "description": "One-day ad exchange game"
            }
        }
        
        # Filter game configs based on allowed games
        if self.allowed_games is not None:
            filtered_configs = {}
            for game_id in self.allowed_games:
                if game_id in self.game_configs:
                    filtered_configs[game_id] = self.game_configs[game_id]
                else:
                    print(f"Unknown game type in allowed_games: {game_id}")
            self.game_configs = filtered_configs
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        address = writer.get_extra_info('peername')
        player_name = None
        
        try:
            # Request device ID
            await self.send_message(writer, {"message": "request_device_id"})
            device_id = await self.receive_message(reader)
            
            if not device_id or device_id.get("message") != "provide_device_id":
                print(f"Invalid device ID response from {address}")
                return
            
            device_id = device_id.get("device_id", f"device_{address[0]}_{address[1]}")
            
            # Request player name
            await self.send_message(writer, {"message": "request_name"})
            name_response = await self.receive_message(reader)
            
            if not name_response or name_response.get("message") != "provide_name":
                print(f"Invalid name response from {address}")
                return
            
            player_name = name_response.get("name", f"Player_{address[0]}_{address[1]}")
            
            # Check for duplicate names
            original_name = player_name
            counter = 1
            while player_name in self.players:
                player_name = f"{original_name}_{counter}"
                counter += 1
            
            # Log if name was modified due to conflict
            if player_name != original_name:
                print(f"Name conflict resolved: '{original_name}' -> '{player_name}'", flush=True)
            
            # Create player connection
            player = PlayerConnection(
                name=player_name,
                reader=reader,
                writer=writer,
                address=address,
                device_id=device_id,
                connected_at=time.time(),
                game_history=[]
            )
            
            self.players[player_name] = player
            
            # Send confirmation
            await self.send_message(writer, {
                "message": "connection_established",
                "name": player_name,
                "available_games": list(self.game_configs.keys())
            })
            
            # Player connected successfully
            if player_name == original_name:
                print(f"Player '{player_name}' connected from {address[0]}:{address[1]} (no name conflicts)", flush=True)
            else:
                print(f"Player '{player_name}' connected from {address[0]}:{address[1]} (resolved from '{original_name}')", flush=True)
            
            # Main client loop
            await self.client_loop(player)
            
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            if player_name and player_name in self.players:
                # Remove player from any games they're in
                if player_name in self.players:
                    player = self.players[player_name]
                    if player.current_game and player.current_game in self.games:
                        game_players = self.games[player.current_game]["players"]
                        # Remove player from game list
                        game_players[:] = [p for p in game_players if p.name != player_name]
                        print(f"Player {player_name} disconnected from {player.current_game} game! ({len(game_players)} players remaining)", flush=True)
                
                del self.players[player_name]
            writer.close()
            await writer.wait_closed()
            if player_name:
                if player.current_game and player.current_game in self.games:
                    remaining_count = len(self.games[player.current_game]['players'])
                    print(f"Player {player_name} disconnected from {player.current_game} game! ({remaining_count} players remaining)", flush=True)
                else:
                    print(f"Player {player_name} disconnected (game no longer active)", flush=True)
            else:
                print(f"Unknown player from {address} disconnected", flush=True)
    
    async def client_loop(self, player: PlayerConnection):
        """Main loop for handling client messages."""
        try:
            # Start heartbeat task for this client
            heartbeat_task = asyncio.create_task(self.send_heartbeat(player))
            
            while True:
                message = await self.receive_message(player.reader, player)
                if not message:
                    break
                
                await self.handle_message(player, message)
                
        except Exception as e:
            self.logger.error(f"error in client loop for {player.name}: {e}")
        finally:
            # Cancel heartbeat task when client disconnects
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
    
    async def send_heartbeat(self, player: PlayerConnection):
        """Send periodic heartbeat messages to keep client alive."""
        try:
            while True:
                await asyncio.sleep(15)  # Send heartbeat every 15 seconds
                
                # Only send heartbeat if client is still connected and waiting
                if (player.current_game and 
                    player.current_game in self.games and 
                    not self.games[player.current_game]["tournament_started"]):
                    
                    await self.send_message(player.writer, {
                        "message": "heartbeat",
                        "game_type": player.current_game,
                        "players_connected": len(self.games[player.current_game]["players"]),
                        "tournament_started": False,
                        "waiting_for_start": True
                    })
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            # Log error but don't crash the heartbeat
            pass
    
    async def handle_message(self, player: PlayerConnection, message: Dict[str, Any]):
        """Handle a message from a client."""
        msg_type = message.get("message")
        
        if msg_type == "ready":
            # Client is ready, no action needed
            pass
        elif msg_type == "join_game":
            await self.handle_join_game(player, message)
        elif msg_type == "provide_action":
            # Store the action for the current round
            player.pending_action = message.get("action")
        elif msg_type == "action":
            # Store the action for the current round
            player.pending_action = message.get("action")
        elif msg_type == "get_action":
            await self.handle_get_action(player, message)
        elif msg_type == "ready_next_round":
            await self.handle_ready_next_round(player, message)
        elif msg_type == "ping":
            await self.send_message(player.writer, {"message": "pong"})
        else:
            self.logger.warning(f"unknown message type from {player.name}: {msg_type}")
    
    async def handle_join_game(self, player: PlayerConnection, message: Dict[str, Any]):
        """Handle a player joining a game."""
        game_type = message.get("game_type")
        
        if game_type not in self.game_configs:
            await self.send_message(player.writer, {
                "message": "error",
                "error": f"Unknown game type: {game_type}"
            })
            return
        
        # Check if player is already in a game
        if player.current_game:
            await self.send_message(player.writer, {
                "message": "error",
                "error": "Already in a game"
            })
            return
        
        # Add player to game queue
        if game_type not in self.games:
            self.games[game_type] = {
                "players": [],
                "game": None,
                "config": self.game_configs[game_type],
                "tournament_started": False
            }
        
        self.games[game_type]["players"].append(player)
        player.current_game = game_type
        
        await self.send_message(player.writer, {
            "message": "joined_game",
            "game_type": game_type,
            "position": len(self.games[game_type]["players"])
        })
        
        # Print player join status for TA
        current_players = len(self.games[game_type]["players"])
        print(f"Player {player.name} joined {game_type} game! ({current_players} players total)", flush=True)
        
        # Inform player about tournament status
        await self.send_message(player.writer, {
            "message": "tournament_status",
            "game_type": game_type,
            "players_connected": len(self.games[game_type]["players"]),
            "tournament_started": self.games[game_type]["tournament_started"],
            "waiting_for_start": True
        })
    
    async def handle_get_action(self, player: PlayerConnection, message: Dict[str, Any]):
        """Handle a get_action request (legacy support)."""
        # This is handled in the game loop, but we keep it for compatibility
        pass
    
    async def handle_ready_next_round(self, player: PlayerConnection, message: Dict[str, Any]):
        """Handle a ready_next_round message."""
        # This is handled in the game loop, but we keep it for compatibility
        pass
    

    
    async def start_tournament(self, game_type: str):
        """Start a tournament with all connected players."""
        self.debug_print(f"start_tournament called for {game_type}")
        game_data = self.games[game_type]
        players = game_data["players"]
        
        self.debug_print(f"Game data: {game_data}")
        self.debug_print(f"Players: {[p.name for p in players]}")
        
        if len(players) < 2:
            self.logger.warning(f"Not enough players to start tournament: {len(players)}")
            self.debug_print(f"Not enough players ({len(players)}), cannot start tournament")
            return
        
        if game_data["tournament_started"]:
            self.logger.warning(f"Tournament already started for {game_type}")
            self.debug_print(f"Tournament already started, cannot start again")
            return
        
        print(f"Starting tournament for {game_type} with {len(players)} players!", flush=True)
        self.debug_print(f"Setting tournament_started to True")
        game_data["tournament_started"] = True
        
        # Announce tournament start to all players
        self.debug_print(f"Announcing tournament start to players")
        for player in players:
            await self.send_message(player.writer, {
                "message": "tournament_start",
                "game_type": game_type,
                "num_players": len(players),
                "num_rounds": game_data["config"]["num_rounds"],
                "players": [p.name for p in players]
            })
        
        # Start lab tournament loop
        self.debug_print(f"Creating tournament task")
        self.debug_print(f"Current event loop: {asyncio.get_running_loop()}")
        task = asyncio.create_task(self.run_lab(game_type, players))
        self.debug_print(f"Tournament task created: {task}")
        self.debug_print(f"Task done: {task.done()}")
        self.debug_print(f"Task pending: {not task.done()}")
    
    async def run_lab(self, game_type: str, players: List[PlayerConnection]):
        """Run a lab tournament with random pairings each round."""
        self.debug_print(f"==========================================")
        self.debug_print(f"run_lab called for {game_type} with {len(players)} players")
        self.debug_print(f"==========================================")
        game_data = self.games[game_type]
        game_config = game_data["config"]
        num_players_per_game = game_config["num_players"]  # 2 for RPS
        total_rounds = game_config["num_rounds"]  # 1000 rounds
        
        self.debug_print(f"Tournament config: num_players_per_game={num_players_per_game}, total_rounds={total_rounds}")
        
        # Track player statistics
        player_stats = {player.name: {"total_reward": 0, "games_played": 0} for player in players}
        
        try:
            print(f"TOURNAMENT {game_type} started with {len(players)} players", flush=True)
            
            # Create all possible pairings once (like old server)
            self.debug_print(f"Creating all possible pairings")
            all_pairings = self.create_round_pairings(players, num_players_per_game)
            self.debug_print(f"Created {len(all_pairings)} total pairings")
            
            if not all_pairings:
                self.logger.warning(f"No valid pairings found")
                self.debug_print(f"No valid pairings, cannot start tournament")
                return
            
            # Run all pairings (each pairing plays num_rounds internally)
            print(f"Running {len(all_pairings)} games, each with {total_rounds} rounds", flush=True)
            self.debug_print(f"Running {len(all_pairings)} games in parallel")
            await self.run_all_pairings(game_type, all_pairings, total_rounds, player_stats)
            self.debug_print(f"Completed all games")
            
            # Tournament finished
            self.debug_print(f"All rounds completed, finishing tournament")
            await self.finish_tournament(game_type, players, player_stats)
            print(f"TOURNAMENT {game_type} ended.", flush=True)
            
        except Exception as e:
            self.logger.error(f"error running {game_type} tournament: {e}")
            self.debug_print(f"Exception in tournament: {e}")
            print(f"error running {game_type} tournament: {e}")
            await self.finish_tournament(game_type, players, player_stats, error=True)
        finally:
            self.debug_print(f"==========================================")
            self.debug_print(f"run_lab method completed for {game_type}")
            self.debug_print(f"==========================================")
    
    async def run_all_pairings(self, game_type: str, pairings: List[List[PlayerConnection]], num_rounds: int, player_stats: Dict):
        """Run all pairings in parallel, each playing num_rounds internally."""
        self.debug_print(f"run_all_pairings called with {len(pairings)} pairings, {num_rounds} rounds each")
        tasks = []
        
        for i, pairing in enumerate(pairings):
            self.debug_print(f"Creating task {i} for pairing: {[p.name for p in pairing]}")
            task = asyncio.create_task(self.run_single_game(game_type, pairing, num_rounds, player_stats))
            tasks.append(task)
        
        self.debug_print(f"Created {len(tasks)} tasks, waiting for completion")
        # Wait for all games to complete
        await asyncio.gather(*tasks)
        self.debug_print(f"All {len(tasks)} tasks completed")
    
    async def run_single_game(self, game_type: str, players: List[PlayerConnection], num_rounds: int, player_stats: Dict):
        """Run a single game between a group of players for multiple rounds."""
        self.debug_print(f"ENTERING run_single_game with game_type: {game_type}, players: {[p.name for p in players]}, rounds: {num_rounds}")
        self.debug_print(f"Player stats at start: {player_stats}")
        game_config = self.game_configs[game_type]
        
        # Initialize history tracking (like old server)
        action_history = []
        utility_history = []
        
        # Create new game instance for this pairing
        if game_type == "auction":
            # Special handling for auction games - use new interface
            player_names = [player.name for player in players]
            
            self.debug_print(f"Creating auction game with players: {player_names}")
            
            game = game_config["game_class"](
                goods={"A", "B", "C", "D"},
                player_names=player_names,
                num_rounds=num_rounds,  # Multiple rounds game
                kth_price=1,
                valuation_type="additive",
                value_range=(10, 50)
            )
            
            self.debug_print(f"Auction game created successfully")
            self.debug_print(f"Game goods: {game.goods}")
            self.debug_print(f"Game players: {game.players}")
            
            # Note: Agents are on the client side, not stored in PlayerConnection
            self.debug_print(f"Auction game created with {len(players)} players")
        elif game_type in ["adx_twoday", "adx_oneday"]:
            num_players = len(players)
            if game_type == "adx_twoday":
                game = game_config["game_class"](num_players=num_players)
            else:  # adx_oneday
                game = game_config["game_class"](num_agents=num_players)
            
            self.debug_print(f"AdX game created successfully")
            self.debug_print(f"Game type: {game_type}")
            self.debug_print(f"Game class: {game_config['game_class']}")
            self.debug_print(f"Number of players: {num_players}")
            self.debug_print(f"Game object: {game}")
        else:
            # For other games, create multi-round game
            game = game_config["game_class"](rounds=num_rounds)
        
        try:
            self.debug_print(f"Initializing game")
            # Initialize game
            obs = game.reset()
            self.debug_print(f"Game type: {game_type}")
            self.debug_print(f"Initial obs: {obs}")
            
            # Run multiple rounds within the same game instance
            for round_num in range(num_rounds):
                self.debug_print(f"Starting round {round_num + 1}/{num_rounds}")
                
                # Special handling for AdX games - generate campaigns and send to players
                if game_type in ["adx_twoday", "adx_oneday"]:
                    self.debug_print(f"Handling AdX game initialization for round {round_num + 1}")
                    self.debug_print(f"Initial obs from game.reset(): {obs}")
                    
                    # For AdX games, we need to send campaign information to each player
                    for i, player in enumerate(players):
                        if i in obs:
                            campaign_info = obs[i]
                            self.debug_print(f"Player {player.name} gets campaign: {campaign_info}")
                            
                            # Update observation with campaign information
                            obs[i] = {
                                "campaign": campaign_info,
                                "round": round_num + 1
                            }
                            self.debug_print(f"Updated observation for {player.name}: {obs[i]}")
                        else:
                            self.debug_print(f"Warning: No campaign info for player {player.name} (index {i})")
                            # Create default campaign info
                            obs[i] = {
                                "campaign": {"id": f"campaign_{i}", "market_segment": "Male", "reach": 100, "budget": 50.0},
                                "round": round_num + 1
                            }
                            self.debug_print(f"Created default campaign for {player.name}: {obs[i]}")
                
                # Special handling for auction games - generate valuations
                if game_type == "auction":
                    self.debug_print(f"Generating valuations for auction game round {round_num + 1}")
                    # Generate valuations for the round
                    game.generate_valuations_for_round()
                    self.debug_print(f"Generated valuations: {game.current_valuations}")
                    
                    # Update observations with goods information and valuations
                    for i, player in enumerate(players):
                        player_name = player.name
                        if player_name in game.current_valuations:
                            obs[i] = {
                                "goods": game.goods,
                                "valuations": game.current_valuations[player_name],
                                "valuation_type": game.valuation_type,
                                "kth_price": game.kth_price,
                                "round": round_num + 1
                            }
                            self.debug_print(f"Sent observation to {player_name}: {obs[i]}")
                        else:
                            self.debug_print(f"Warning: No valuations found for player {player_name}")
                            # Fallback observation
                            obs[i] = {
                                "goods": game.goods,
                                "valuations": [0] * len(game.goods),
                                "valuation_type": game.valuation_type,
                                "kth_price": game.kth_price,
                                "round": round_num + 1
                            }
                
                # Get actions from all players
                self.debug_print(f"Getting actions from players for round {round_num + 1}")
                actions = {}
                for i, player in enumerate(players):
                    # Clear any pending action
                    player.pending_action = None
                    
                    # Update observation with round information
                    player_obs = obs.get(i, {})
                    if not player_obs or player_obs == {}:
                        # For games that don't provide observations, provide basic round information
                        player_obs = {"round": round_num + 1, "game_type": game_type}
                    else:
                        # For games that provide observations (like matrix games), ensure round is included
                        player_obs["round"] = round_num + 1
                    
                    # Request action
                    self.debug_print(f"Requesting action from {player.name}")
                    await self.send_message(player.writer, {
                        "message": "request_action",
                        "round": round_num + 1,
                        "observation": player_obs
                    })
                    
                    # Wait for action response with timeout
                    timeout = 5.0
                    start_time = time.time()
                    while player.pending_action is None and (time.time() - start_time) < timeout:
                        await asyncio.sleep(0.1)
                    
                    if player.pending_action is not None:
                        actions[i] = player.pending_action
                        self.debug_print(f"Received action from {player.name}: {player.pending_action}")
                    else:
                        # Use default action if timeout
                        actions[i] = self.get_default_action(game_type)
                        self.logger.warning(f"Timeout waiting for action from {player.name}, using default")
                        self.debug_print(f"Using default action for {player.name}: {actions[i]}")
                
                self.debug_print(f"All actions collected for round {round_num + 1}: {actions}")
                
                # Step the game
                self.debug_print(f"Stepping the game for round {round_num + 1}")
                obs, rewards, done, info = game.step(actions)
                self.debug_print(f"Game step completed for round {round_num + 1}")
                self.debug_print(f"New obs: {obs}")
                self.debug_print(f"Rewards: {rewards}")
                self.debug_print(f"Done: {done}")
                self.debug_print(f"Info: {info}")
                
                # Track action and utility history (like old server)
                action_history.append(actions.copy())
                utility_history.append([rewards.get(i, 0) for i in range(len(players))])
                
                # Debug output for auction games
                if game_type == "auction":
                    self.debug_print(f"Actions: {actions}")
                    self.debug_print(f"Rewards: {rewards}")
                    self.debug_print(f"Info: {info}")
                
                # Debug output for AdX games
                if game_type in ["adx_twoday", "adx_oneday"]:
                    self.debug_print(f"AdX Actions: {actions}")
                    self.debug_print(f"AdX Rewards: {rewards}")
                    self.debug_print(f"AdX Info: {info}")
                    self.debug_print(f"AdX Done: {done}")
                    
                    # Check if rewards are all zero
                    if all(reward == 0 for reward in rewards.values()):
                        self.debug_print(f"WARNING: All AdX rewards are zero! This might indicate a scoring issue.")
                        self.debug_print(f"Game state after step: {game.get_game_state() if hasattr(game, 'get_game_state') else 'No get_game_state method'}")
                        self.debug_print(f"Game type: {type(game)}")
                        self.debug_print(f"Game methods: {[method for method in dir(game) if not method.startswith('_')]}")
                
                # Update player statistics
                self.debug_print(f"Updating player statistics for round {round_num + 1}")
                for i, player in enumerate(players):
                    reward = rewards.get(i, 0)
                    player_stats[player.name]["total_reward"] += reward
                    player_stats[player.name]["games_played"] += 1
                    
                    # Update PlayerConnection object for dashboard
                    player.total_reward += reward
                    player.games_played += 1
                    
                    self.debug_print(f"Player {player.name} got reward {reward}, total now {player_stats[player.name]['total_reward']}")
                
                # Send results to players and update agents
                self.debug_print(f"Sending results to players for round {round_num + 1}")
                for i, player in enumerate(players):
                    reward = rewards.get(i, 0)
                    player_obs = obs.get(i, {})
                    player_action = actions.get(i, {})
                    player_info = info.get(i, {})
                    
                    # Add to player's game history (like old server)
                    game_result = {
                        "round": round_num + 1,
                        "reward": reward,
                        "action": player_action,
                        "opponent_actions": {j: actions[j] for j in range(len(players)) if j != i},
                        "info": player_info,
                        "action_history": action_history.copy(),
                        "utility_history": utility_history.copy()
                    }
                    player.game_history.append(game_result)
                    
                    # Note: Agents are updated on the client side, not here
                    
                    await self.send_message(player.writer, {
                        "message": "round_result",
                        "round": round_num + 1,
                        "reward": reward,
                        "opponent_actions": {j: actions[j] for j in range(len(players)) if j != i},
                        "info": player_info,
                        "action_history": action_history.copy(),
                        "utility_history": utility_history.copy()
                    })
                
                # Check if game is done
                if done:
                    self.debug_print(f"Game completed after {round_num + 1} rounds")
                    break
                
                # Small delay between rounds
                await asyncio.sleep(0.1)
                
            self.debug_print(f"Multi-round game completed successfully")
                
        except Exception as e:
            self.debug_print(f"Exception in single game for {game_type}: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Error in single game for {game_type}: {e}")
    
    async def send_round_summary(self, players: List[PlayerConnection], round_num: int, player_stats: Dict):
        """Send round summary to all players."""
        # Calculate rankings
        rankings = sorted(player_stats.items(), key=lambda x: x[1]["total_reward"], reverse=True)
        
        for player in players:
            player_rank = next(i for i, (name, _) in enumerate(rankings) if name == player.name) + 1
            avg_reward = player_stats[player.name]["total_reward"] / max(player_stats[player.name]["games_played"], 1)
            
            await self.send_message(player.writer, {
                "message": "round_summary",
                "round": round_num + 1,
                "rank": player_rank,
                "total_reward": player_stats[player.name]["total_reward"],
                "games_played": player_stats[player.name]["games_played"],
                "average_reward": avg_reward,
                "top_players": [name for name, _ in rankings[:5]]  # Top 5 players
            })
    
    async def finish_tournament(self, game_type: str, players: List[PlayerConnection], player_stats: Dict, error: bool = False):
        """Finish tournament and send final results."""
        # Calculate final rankings
        rankings = sorted(player_stats.items(), key=lambda x: x[1]["total_reward"], reverse=True)
        
        # Prepare final results
        results = {
            "game_type": game_type,
            "tournament": True,
            "players": [p.name for p in players],
            "total_rounds": self.game_configs[game_type]["num_rounds"],
            "final_rankings": rankings,
            "error": error
        }
        
        # Send final results to all players
        for player in players:
            player_rank = next(i for i, (name, _) in enumerate(rankings) if name == player.name) + 1
            final_reward = player_stats[player.name]["total_reward"]
            games_played = player_stats[player.name]["games_played"]
            
            await self.send_message(player.writer, {
                "message": "tournament_end",
                "results": results,
                "final_rank": player_rank,
                "final_reward": final_reward,
                "games_played": games_played,
                "average_reward": final_reward / max(games_played, 1)
            })
        
        # Store results
        self.results.append(results)
        
        # Print final leaderboard
        print(f"FINAL LEADERBOARD for {game_type}:", flush=True)
        for rank, (player_name, stats) in enumerate(rankings, 1):
            avg_reward = stats["total_reward"] / max(stats["games_played"], 1)
            print(f"  #{rank}: {player_name} - Total: {stats['total_reward']:.2f}, Games: {stats['games_played']}, Avg: {avg_reward:.2f}", flush=True)
        
        # Clean up tournament
        if game_type in self.games:
            del self.games[game_type]
        
        print(f"Tournament {game_type} finished", flush=True)
    
    def get_default_action(self, game_type: str):
        """Get a default action for a game type."""
        if game_type == "rps":
            return 0  # rock
        elif game_type in ["bos", "bosii"]:
            return 0  # first action
        elif game_type == "chicken":
            return 0  # swerve
        elif game_type == "lemonade":
            return 0  # position 0
        elif game_type == "auction":
            return {"A": 0, "B": 0, "C": 0, "D": 0}  # zero bids
        elif game_type in ["adx_oneday", "adx_twoday"]:
            # For AdX games, we need to create a default OneDayBidBundle
            # This is a fallback and shouldn't normally be used
            from core.game.AdxOneDayGame import OneDayBidBundle
            from core.game.bid_entry import SimpleBidEntry
            from core.game.market_segment import MarketSegment
            
            # Create a minimal bid bundle with no bids
            return OneDayBidBundle(
                campaign_id=0,
                day_limit=0.0,
                bid_entries=[]
            )
        else:
            return 0
    
    def create_round_pairings(self, players: List[PlayerConnection], num_per_game: int) -> List[List[PlayerConnection]]:
        """Create all possible pairings for a tournament round (like old server)."""
        from itertools import permutations, combinations
        
        self.debug_print(f"create_round_pairings called with {len(players)} players, {num_per_game} per game")
        
        # Get player addresses (like old server)
        player_addresses = list(players)
        
        # Check if order matters (like old server)
        # For most games, order doesn't matter, so we use combinations
        # But we can make this configurable if needed
        order_matters = False  # Set to True if player order matters for the game
        
        if order_matters:
            pairings = list(permutations(player_addresses, r=num_per_game))
        else:
            pairings = list(combinations(player_addresses, r=num_per_game))
        
        # Convert to list of lists
        pairings = [list(pairing) for pairing in pairings]
        
        self.debug_print(f"Created {len(pairings)} pairings using {'permutations' if order_matters else 'combinations'}")
        self.debug_print(f"First few pairings: {[[p.name for p in pairing] for pairing in pairings[:3]]}")
        
        return pairings
    

    
    async def send_message(self, writer: asyncio.StreamWriter, message: Dict[str, Any]):
        """Send a message to a client."""
        try:
            # Convert sets to lists for JSON serialization
            def convert_sets(obj):
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_sets(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets(item) for item in obj]
                else:
                    return obj
            message = convert_sets(message)
            data = json.dumps(message).encode() + b'\n'
            # Sending message to client - no logging needed
            writer.write(data)
            await writer.drain()
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def receive_message(self, reader: asyncio.StreamReader, player: Optional[PlayerConnection] = None) -> Optional[Dict[str, Any]]:
        """Receive a message from a client."""
        try:
            if player and player.read_lock:
                async with player.read_lock:
                    data = await reader.readline()
                    if not data:
                        return None
                    decoded_data = data.decode().strip()
                    if not decoded_data:
                        return None
                    try:
                        msg = json.loads(decoded_data)
                        return msg
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error from {player.name if player else 'unknown'}: {e}")
                        print(f"Raw data: {repr(decoded_data)}")
                        return None
            else:
                data = await reader.readline()
                if not data:
                    return None
                decoded_data = data.decode().strip()
                if not decoded_data:
                    return None
                try:
                    msg = json.loads(decoded_data)
                    return msg
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Raw data: {repr(decoded_data)}")
                    return None
        except Exception as e:
            print(f"Error receiving message: {e}")
        return None
    
    def debug_print(self, message: str, flush: bool = True):
        """Print debug message only if verbose mode is enabled."""
        if self.verbose:
            print(f"[SERVER DEBUG] {message}", flush=flush)
    
    async def start(self):
        """Start the server."""
        try:
            if self.verbose:
                print(f"[DEBUG] Attempting to start server on {self.host}:{self.port}")
                print(f"[DEBUG] Allowed games: {self.allowed_games}")
                print(f"[DEBUG] Game configs: {list(self.game_configs.keys())}")
            
            server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            
            print(f"AGT Tournament Server", flush=True)
            print("=====================", flush=True)
            print(f"Server running on {self.host}:{self.port}", flush=True)
            if self.allowed_games is not None:
                print(f"Game restrictions: {', '.join(self.allowed_games)}", flush=True)
            else:
                print("No game restrictions: all games available", flush=True)
            print("Commands:", flush=True)
            print("  Ctrl+Z                - Start tournaments", flush=True)
            print("  Ctrl+C                - Exit server", flush=True)
            print("", flush=True)
            print("Waiting for players to connect...", flush=True)
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"[ERROR] Failed to start AGT server: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            raise
    
    def save_results(self):
        """Save game results to file."""
        if self.results:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"results/agt_server_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"Results saved to {filename}")


async def main():
    """Main server function."""
    parser = argparse.ArgumentParser(description='AGT Server for Lab Competitions')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--config', type=str, help='Configuration file (required if no game specified)')
    parser.add_argument('--game', type=str, choices=['rps', 'bos', 'bosii', 'chicken', 'pd', 'lemonade', 'auction', 'adx_twoday', 'adx_oneday'],
                       help='Restrict server to a specific game type (required if no config specified)')
    parser.add_argument('--games', type=str, nargs='+', 
                       choices=['rps', 'bos', 'bosii', 'chicken', 'pd', 'lemonade', 'auction', 'adx_twoday', 'adx_oneday'],
                       help='Restrict server to specific game types (multiple allowed, required if no config specified)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose debug output (shows all debug messages)')
    # Dashboard is now separate - run with: python dashboard/app.py

    
    args = parser.parse_args()
    
    # Default configuration
    config = {
        "server_name": "AGT Lab Server",
        "max_players": 100,
        "timeout": 30,
        "save_results": True
    }
    
    # Load custom config if provided
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config.update(json.load(f))
    
    # Require either a config file or game specification
    if not args.config and not args.game and not args.games:
        print("ERROR: Server requires either a config file (--config) or game specification (--game or --games)")
        print("This ensures all players join the same server with the same game type.")
        print("Example: python server.py --game rps")
        print("Example: python server.py --config lab01_rps.json")
        return
    
    # Set allowed games based on command line arguments
    if args.game:
        config["allowed_games"] = [args.game]
        print(f"server restricted to game: {args.game}")
    elif args.games:
        config["allowed_games"] = args.games
        print(f"server restricted to games: {', '.join(args.games)}")
    elif args.config:
        # If config file is provided but no games specified, require games in config
        if "allowed_games" not in config:
            print("ERROR: Config file must specify 'allowed_games'")
            print("Example config: {\"allowed_games\": [\"rps\"]}")
            return
    
    server = AGTServer(config, args.host, args.port, args.verbose)
    
    # Flag to track if tournaments have been started
    tournaments_started = False
    
    async def start_tournaments():
        """Start tournaments for all active games."""
        # Start tournaments for all games that have players
        for game_type, game_data in server.games.items():
            if len(game_data["players"]) >= 2 and not game_data["tournament_started"]:
                print(f"Starting tournament for {game_type} with {len(game_data['players'])} players")
                await server.start_tournament(game_type)
        
        # Wait for all tournaments to complete
        while any(game_data["tournament_started"] for game_data in server.games.values()):
            await asyncio.sleep(1)
        
        print("All tournaments completed!")
        server.save_results()
    
    def signal_handler(signum, frame):
        nonlocal tournaments_started
        if signum == signal.SIGTSTP:
            # SIGTSTP (Ctrl+Z) = Start tournaments
            if not tournaments_started:
                print("\nStarting tournaments for all active games...")
                tournaments_started = True
                # Schedule tournament start in the event loop
                asyncio.create_task(start_tournaments())
        elif signum == signal.SIGINT:
            # SIGINT (Ctrl+C) = Exit server
            print("\n🛑 Shutting down server...")
            server.save_results()
            sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGTSTP, signal_handler)  # Start tournaments (Ctrl+Z)
    signal.signal(signal.SIGINT, signal_handler)   # Exit server (Ctrl+C)
    
    print("AGT Tournament Server")
    print("=====================")
    print("Commands:")
    print("  Ctrl+Z                - Start tournaments")
    print("  Ctrl+C                - Exit server")
    print("")
    print("Dashboard: Run 'python dashboard/app.py' in a separate terminal")
    print("")
    
    try:
        # Dashboard is now separate - run with: python dashboard/app.py
        
        # Start server
        print(f"[DEBUG] Creating server task...")
        server_task = asyncio.create_task(server.start())
        
        # Wait for manual interrupt to start tournaments
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        server.save_results()
        raise


if __name__ == "__main__":
    asyncio.run(main()) 