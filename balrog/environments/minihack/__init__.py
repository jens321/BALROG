from nle.language_wrapper.wrappers.nle_language_wrapper import NLELanguageWrapper

from nle_code_wrapper.wrappers.nle_code_wrapper import NLECodeWrapper

ACTIONS = {
    "north": "move north",
    "east": "move east",
    "south": "move south",
    "west": "move west",
    "northeast": "move northeast",
    "southeast": "move southeast",
    "southwest": "move southwest",
    "northwest": "move northwest",
    "far north": "move far north",
    "far east": "move far east",
    "far south": "move far south",
    "far west": "move far west",
    "far northeast": "move far northeast",
    "far southeast": "move far southeast",
    "far southwest": "move far southwest",
    "far northwest": "move far northwest",
    "up": "go up the stairs",
    "down": "go down the stairs",
    "wait": "rest one move while doing nothing",
    "more": "display more of the message",
    "apply": "apply (use) a tool",
    "close": "close an adjacent door",
    "open": "open an adjacent door",
    "eat": "eat something",
    "force": "force a lock",
    "kick": "kick an enemy or a locked door or chest",
    "loot": "loot a box on the floor",
    "pickup": "pick up things at the current location if there are any",
    "pray": "pray to the gods for help",
    "puton": "put on an accessory",
    "quaff": "quaff (drink) something",
    "search": "search for hidden doors and passages",
    "zap": "zap a wand",
}

CODE_INSTRUCTION_PROMPT = """
You are an agent playing MiniHack. The following are the possible high-level actions you can take in the game, followed by a short description of each action:

{skill_list}

In each observation of the game, you will receive both a textual observation as well as a character-based one. Here is a legend for what each character represents in the character-based observation:
    @: the player
    #: a corridor
    +: a closed door
    |: a vertical wall
    -: a horizontal wall
    .: the floor
    <: stairs leading up
    >: stairs leading down

In a moment I will present a history of high-level actions and observations from the game.

Tip: there is no point in outputting the same action over and over if nothing changes.

PLAY!
"""

STRATEGY_TO_DESC = {
    "explore_corridor": "explores the corridor",
    "explore_corridor_east": "explores the corridor to the east",
    "explore_corridor_north": "explores the corridor to the north",
    "explore_corridor_south": "explores the corridor to the south",
    "explore_corridor_systematically": "explores the corridor systematically",
    "explore_corridor_systematically_east": "explores the corridor systematically to the east",
    "explore_corridor_systematically_north": "explores the corridor systematically to the north",
    "explore_corridor_systematically_south": "explores the corridor systematically to the south",
    "explore_corridor_systematically_west": "explores the corridor systematically to the west",
    "explore_corridor_west": "explores the corridor to the west",
    "explore_room": "explores the room",
    "explore_room_east": "explores the room to the east",
    "explore_room_north": "explores the room to the north",
    "explore_room_south": "explores the room to the south",
    "explore_room_systematically": "explores the room systematically",
    "explore_room_systematically_east": "explores the room systematically to the east",
    "explore_room_systematically_north": "explores the room systematically to the north",
    "explore_room_systematically_south": "explores the room systematically to the south",
    "explore_room_systematically_west": "explores the room systematically to the west",
    "explore_room_west": "explores the room to the west",
    "explore_items": "explores the items",
    "goto_closest_corridor": "navigates the agent towards the closest corridor",
    "goto_closest_corridor_east": "navigates the agent towards the closest corridor to the east",
    "goto_closest_corridor_north": "navigates the agent towards the closest corridor to the north",
    "goto_closest_corridor_south": "navigates the agent towards the closest corridor to the south",
    "goto_closest_corridor_west": "navigates the agent towards the closest corridor to the west",
    "goto_closest_room": "navigates the agent towards the closest room",
    "goto_closest_room_east": "navigates the agent towards the closest room to the east",
    "goto_closest_room_north": "navigates the agent towards the closest room to the north",
    "goto_closest_room_south": "navigates the agent towards the closest room to the south",
    "goto_closest_room_west": "navigates the agent towards the closest room to the west",
    "goto_closest_staircase_down": "navigates the agent towards the closest stairs leading down",
    "goto_closest_staircase_up": "navigates the agent towards the closest stairs leading up",
    "goto_closest_unexplored_corridor": "navigates the agent towards the closest unexplored corridor",
    "goto_closest_unexplored_room": "navigates the agent towards the closest unexplored room",
    "open_doors": "opens doors",
    "open_doors_kick": "opens doors by kicking them",
    "search_corridor_for_hidden_doors": "searches the corridor for hidden doors",
    "search_room_for_hidden_doors": "searches the room for hidden doors",
}


def get_available_actions(env):
    available_actions = {}
    for action in env.actions:
        action_key = NLELanguageWrapper.all_nle_action_map[action][0]
        if action_key not in ACTIONS:
            continue
        available_actions[action_key] = ACTIONS[action_key]
    return available_actions


def get_goal_from_task_name(task: str):
    if "corridor" in task.lower():
        goal = "Your goal is to explore the level, potentially fight monsters, and reach the stairs down."
    elif "quest" in task.lower():
        goal = "Your goal is to explore the level, fight monsters, and navigate rooms and mazes to ultimately reach the stairs down."
    elif "boxoban" in task.lower():
        goal = "You are playing Boxoban, a box-pushing game inspired by Sokoban. Your goal is to push the boulders onto the fountains on the map. You can push the boulders by walking into them, as long as there are no obstacles behind them."
    elif "key" in task.lower():
        goal = "Your goal is to find the key, use it to unlock the door, and then reach the stairs down."
    elif "river" in task.lower():
        goal = "Your goal is to reach the stairs down at the other side of the river."
    elif "hidenseek" in task.lower():
        goal = "Your goal is to avoid the monsters and reach the stairs down."
    else:
        goal = "Your goal is to get as far as possible in the game."

    return goal


def get_instruction_prompt(env, task="MiniHack-ExploreMaze-Hard-Mapped-v0"):
    goal = get_goal_from_task_name(task)

    if isinstance(env, NLECodeWrapper):
        strategies = [s.__name__ for s in env.bot.strategies]
        skill_list = ""
        for idx, s in enumerate(strategies, 1):
            skill_list += f"- {s}: {STRATEGY_TO_DESC[s]}\n"
        instruction_prompt = CODE_INSTRUCTION_PROMPT.format(skill_list=skill_list)
    else:
        available_actions = get_available_actions(env)
        action_strings = ",\n".join(f"{action}: {description}" for action, description in available_actions.items())
        instruction_prompt = f"""
You are an agent playing MiniHack. The following are the possible actions you can take in the game, followed by a short description of each action:

{action_strings}.

In a moment I will present a history of actions and observations from the game.

Tip: there is no point in outputting the same action over and over if nothing changes.

{goal}

PLAY!
""".strip()

    return instruction_prompt
