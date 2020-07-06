# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 12:22:38 2020

A program to provide a quick summary of a Lichess user's playing style by 
acessing the games played by them (as a given colour) using the Lichess API.

Information that may be useful:
    > Most common openings/variations played
    > Most common moves played against a given sequence of moves
    > Most common game ending status for a given opening, e.g. player often 
        time outs when playing against Slav Defense in blitz


@author: georgems
"""

import itertools

import pandas as pd
import berserk        # Lichess API


#%% ==== FUNCTIONS ====
def get_player_games(**kwargs):
    """
    Exports the games by the given player using berserk API, and returns the 
    winner, game ending status, opening name, and moves as a DataFrame.

    Parameters
    ----------
    **kwargs : various
        The kwargs required by the export_by_player() method. 
        N.B. use strings rather than bool, e.g. "true" rather than True.

    Returns
    -------
    games_df : DataFrame
        DataFrame of where each row is a game.

    """
    # Get games from server
    games_list = list(client.games.export_by_player(**kwargs))
    
    # Entries under "opening" must be converted from dictionary by making the
    # dictionary keys new cols in the df
    games_df = pd.DataFrame([{**x, **x.pop("opening")} for x in games_list])
    games_df = games_df[["winner", "status", "name", "moves"]]
    
    # For each opening, extract the opening name (before the colon) and the 
    # variation name (after the colon) and store in seperate columns
    games_df["opening"] = games_df.name.str.extract("(.*)\:", expand=False)
    games_df["variation"] = games_df.name.str.extract("\:(.*)", expand=False)
    
    # Some openings don't specify a variation
    no_variation_mask = games_df.opening.isnull()
    games_df.opening[no_variation_mask] = games_df.name[no_variation_mask]

    games_df.drop("name", axis=1, inplace=True)
    
    # Split the move list string into a list of strings - each entry a ply
    games_df.moves = games_df.moves.apply(lambda x: x.split())

    return games_df


def given_move_responses(df, moves, color = None, shuffle = True):
    """
    Given a sequence of moves and a dataframe of games, return a dataframe of
    the games that start with [username]'s opponent making those moves.

    Parameters
    ----------
    df : DataFrame
       The DataFrame of games.
    moves : list of str
        List of the moves, e.g. ["e4", "Ke2"].
    color : str, optional
        The colour of the player making the given moves. If color is not given
        then search for the exact move sequence.
    shuffle : bool, optional
        Whether to include permutations of the moves. The default is True.

    Returns
    -------
    DataFrame
        A subset of the input DataFrame.

    """
    
    if shuffle == True:
        moves = itertools.permutations(moves)
    else:
        moves = [moves]
    
    mask = pd.Series([0]*df.shape[0])
    
    # If colour is white then search for moves in even indices, and vice versa
    if color == "white":
        for item in moves:
            mask += df.moves.apply(lambda x: x[0:2*len(item):2] == list(item))
    if color == "black":
        for item in moves:
            mask += df.moves.apply(lambda x: x[1:2*len(item)+1:2] == list(item))
    else:
        for item in moves:
            mask += df.moves.apply(lambda x: x[0:len(item)] == list(item))
        
    return df[mask.astype(bool)]


#%% ==== LOAD DATA ====
client = berserk.Client()

# Input the user, the color they're playing as, and time control
user = "stopcheckingmeout"
perf = "none"
color = "black"

games_df = get_player_games(username = user, 
                            max = 30, 
                            perf_type = perf, 
                            color = color,
                            opening = "true")

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
     print(games_df)


if color == "black":
    opposite_color = "white"
else:
    opposite_color = "black"
    
    
win_mask = (games_df.winner == color)
lose_mask = (games_df.winner == opposite_color)
not_win_mask = ((games_df.winner == opposite_color) | (games_df.winner.isnull()))


    
        
print("Most common openings as " + color + ":")
print(games_df.opening.value_counts())
print()
print("Most common reasons for not winning as " + color + ":")
print(games_df[not_win_mask].status.value_counts())

# print(given_move_responses(games_df, ["c6"], "black"))

