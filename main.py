#Brass Birmingham Board Game Simulation using a parameterized model and a simple genetric algorithm
# Import necessary libraries
import random
import csv
import os
import copy

"""
Each action will have two modes "test" and "perform"
    self.test is a boolean indicating if we are in test mode or perform mode
    In test mode, when an action fails, a string is returned indicating why the action failed, otherise the object is modified according to the aciton
    In perform mode, when an action fails, an exception is thrown (this helps with error tracing)
"""

industry_data = {}
csv_path = os.path.join(os.path.dirname(__file__), "industry_data.csv")
with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        key = f"{row['Industry']}{row['Sequence']}"
        industry_data[key] = dict(row)

class Sub_Action_Controller:
    def __init__(self, test_mode = False, header_flag: bool = False, indent_baseline: int = 0, starting_state_flag: bool = False, action_list_flag: bool = False,
                 action_performed_flag: bool = False, action_detail_flag: bool = False, ending_state_flag: bool = False,
                 blank_line_flag: bool = False, series_mode_flag: bool = False):
        '''
        A complete action print can looks like this at most:
        Header (^header_flag): Tells what this indented section is for
            *Indent (^indent_baseline): keeps the lines indented for readability under the header, actual indent is baseline + 2 spaces (if header_flag is True)
            Starting Game State (): shows the game state before the action is performed
            Possible Action List (): shows the possible actions that can be performed, would need to be provided by the game state
            Performing Action (): action being performed
                Action part
                Action part ...
            Ending Game State (): shows the game state after the action is performed
            Blank Line (): prints a blank line for readibility
        '''
        #Save all of the flags to this sub action controller
        self.test_mode = test_mode
        self.header_flag = header_flag
        self.indent_baseline = indent_baseline
        self.indent = self.indent_baseline + (2 if header_flag else 0)  # Indent is baseline + 2 spaces if header_flag is True
        self.starting_state_flag = starting_state_flag
        self.action_list_flag = action_list_flag
        self.action_performed_flag = action_performed_flag
        self.action_detail_flag = action_detail_flag
        self.ending_state_flag = ending_state_flag
        self.blank_line_flag = blank_line_flag
        # Set a single flag "verbose" if any of the above flags are True
        self.verbose = any([self.header_flag, self.starting_state_flag, self.action_list_flag, self.action_performed_flag, 
                            self.action_detail_flag, self.ending_state_flag, self.blank_line_flag])
        # Series mode flag, if True, then the header and starting state are not printed for each action, only the first action
        self.series_mode_flag = series_mode_flag #Default is parallel mode where headers are re-printed every time
        self.series_header_disable = False #Skips repeating of header & starting state

    def indent_pr(self, message: str):
        # Print the message with the appropriate indentation
        print(" " * self.indent + message)
    
    def restart_series(self):
        # Start a series of actions, disables the header printing
        self.series_header_disable = False
    
    def start_action(self, game: "Game_State" = None, header: str = None, action_list: list["Action"] = None, action: "Action" = None):
        if self.header_flag and not self.series_header_disable:
            # Print the header if header_flag is True
            if header is None:
                raise ValueError("Header must be provided if header_flag is True.")
            self.indent_pr(header)
        if self.starting_state_flag and not self.series_header_disable:
            # Print the starting game state
            if game is None:
                raise ValueError("Game state must be provided if starting_state_flag is True.")
            self.indent_pr("Starting " + game.string_print())
        if self.action_list_flag:
            # Print the possible actions that can be performed
            if action_list is None:
                raise ValueError("Action list must be provided if action_list_flag is True.")
            self.indent_pr("Possible Actions: " + ", ".join([action.action_string for action in action_list]))
        if self.action_performed_flag:
            # Print the action being performed
            if action is None:
                raise ValueError("Action must be provided if action_performed_flag is True.")
            self.indent_pr(f"Performing Action: {action.action_string}")
        if self.series_mode_flag:
            # Disable the header and starting state printing for the series mode
            self.series_header_disable = True

    def end_action(self, game: "Game_State" = None):
        if self.ending_state_flag:
            # Print the ending game state
            if game is None:
                raise ValueError("Game state must be provided if ending_state_flag is True.")
            self.indent_pr("Ending " + game.string_print())
        if self.blank_line_flag:
            # Print a blank line if blank_line_flag is True
            self.indent_pr("")

    def record_action_detail(self, object, name, delta = None, new_value = None):
        # Print the sub action being performed
        if not self.action_detail_flag:
            return
        # If object is a Player, append ".P<player_id>" to name
        if isinstance(object, Player):
            name = f"P{object.player_id}.{name}"
        elif isinstance(object, Played_Industry):
            # Use the industry tile name, omitting the "P" from the player id
            name = f"{object.properties.name}.{name}"
        # Print the action taken
        if delta is not None:
            self.indent_pr(f"  {name} changed by {delta}")
        elif new_value is not None:
            self.indent_pr(f"  {name} changed to {new_value}")

class Action_Controller:
    """
    This class acts as the controller for all actions through flags
        v: boolean, determines if the the game components record all changes to the sub_action_hitory
        sub_action_verbose: boolean, determiens if each sub action is printed as it is changed
        test_mode_flag: boolean, determines if when action fails a string is returned or a exception is thrown
    What modes should we have and what should be thier associated flags?
        perform mode (perform_verbose): 
        test mode (test_verbose): 
    Some common modes that could be used:
    """

    def __init__(self, record: bool = False, verbose: bool = False, test_mode: bool = False, 
                 sub_controller: "Action_Controller" = "minimum"):
        self.sub_controller = Sub_Action_Controller(
            header_flag: bool = False, indent_baseline: int = 0, starting_state_flag: bool = False, action_list_flag: bool = False,
            action_performed_flag: bool = False, action_detail_flag: bool = False, ending_state_flag: bool = False,
            blank_line_flag: bool = False, series_mode_flag: bool = False
        )
        self.mode = "hello"
        if self.mode == "hello"
        #Setup some common sub Action Controller modes
        self.record_actions_flag = record #Creates a record of sub actions
        if record == False and verbose == True:
            raise ValueError("Verbose mode cannot be used without record mode.")
        self.sub_action_verbose = verbose #Prints all sub action statements
        self.test_mode_flag = test_mode #Prevents thown excpetions, used to see if moves are valid
        self.main_action_history = [] #List of all main actions taken
        self.sub_action_history = [] #List of all sub actions taken
        # The sub_controller is used to pass the controller to sub actions, if it is not None
        # If it is None, a sub_controller is created with minimal settings
        # The sub_controller is used when testing actions
        if sub_controller == "minimum":
            # Create a minimal sub controller with no recording or verbose mode
            self.sub_controller = Action_Controller(record=False, verbose=False, test_mode=True, sub_controller=None)
        else:
            self.sub_controller = sub_controller
    
    def start_main_action(self, action: "Action", game: "Game_State"):
        if self.record_actions_flag:
            # Start a new main action and append it to the main action history
            if self.sub_action_verbose:
                if self.test_mode_flag:
                    print("Starting " + game.string_print())
                    print(f"Testing action: {action.action_string}")
                else:
                    #When the controller is started, print the first game state
                    if len(self.main_action_history) == 0:
                        print("Starting " + game.string_print())
                    print(f"Performing action: {action.action_string}")
            self.main_action_history.append(action)
            # Start a new sub action history for this main action
            self.sub_action_history.append([])
    
    def end_main_action(self, game: "Game_State"):
        if self.sub_action_verbose:
            # Print ending game state for each test if in test mode, otherwise print the game state
            if self.test_mode_flag:
                print(f"  Successful action")
                print("Ending " + game.string_print())
                print()
            else:
                print(game.string_print())
    
    def start_game_completion(self, game: "Game_State"):
        if self.sub_action_verbose:
            # Print starting game state
            print()
            print("GAME COMPLETION MODE")
            print(game.string_print(action_history_flag=True))
    
    def next_game_completion(self, chosen_child: "Game_State", valid_children: list["Game_State"]):
        #Print the child choices, and print the selected choice
        if self.record_actions_flag:
            # Record the sub actions, using the settings of this controller
            chosen_child_controller = Action_Controller(
                record=self.record_actions_flag,
                verbose=False,
                test_mode=self.test_mode_flag,
                sub_controller=self.sub_controller
            )
            chosen_child.parent.take_action_copy(chosen_child.previous_action, chosen_child_controller)
        if self.sub_action_verbose:
            # Print next game state
            print(f"Choosing between: {[g.previous_action.action_string for g in valid_children]}")
            print("Chosen:", chosen_child.string_print(action_history_flag=False))

    def record(self, object, name, delta = None, new_value = None):
        if not self.record_actions_flag:
            # If the record_actions_flag is not set, then do not record the action
            return
        # If object is a Player, append ".P<player_id>" to name
        if isinstance(object, Player):
            name = f"P{object.player_id}.{name}"
        elif isinstance(object, Played_Industry):
            # Use the industry tile name, omitting the "P" from the player id
            name = f"{object.properties.name}.{name}"
        if self.sub_action_verbose:
            # If the sub_action_verbose flag is set, then print the action taken
            if delta is not None:
                print(f"  {name} changed by {delta}")
            elif new_value is not None:
                print(f"  {name} changed to {new_value}")
        # Append to sub_action_history
        self.sub_action_history[-1].append({
            "name": name,
            "delta": delta,
            "new_value": new_value
        })
    
    def test(self, string: str):
        #Test the action string and return a string if the action is invalid
        if self.test_mode_flag:
            if self.sub_action_verbose:
                #If the sub_action_verbose flag is set, then print the action taken
                print(f"  Error in action: {string}")
                print()
            #If test mode is on, then return a string if the action is invalid
            return string
        else:
            #If test mode is off, then raise an exception if the action is invalid
            raise ValueError(string)
    


class Industry_Properties:
    def __init__(self, name, csvData):
        self.name = name
        self.industry = csvData['Industry']
        self.industry_type = csvData['Industry Type']
        self.level = int(csvData['Level'])
        self.count = int(csvData['Count'])
        self.sequence = int(csvData['Sequence'])
        self.type_total = int(csvData['Type Total'])
        self.money_cost = int(csvData['Money Cost'])
        self.coal_cost = int(csvData['Coal Cost']) if csvData['Coal Cost'] else 0
        self.iron_cost = int(csvData['Iron Cost']) if csvData['Iron Cost'] else 0
        self.age_restriction = csvData['Age Resttriction'] #Empty string if no age restriction, otherwise "canal" or "rail"
        self.beer_cost = int(csvData['Beer Cost']) if csvData['Beer Cost'] else 0
        self.development_restriction = True if csvData['Development Restriction'] else False
        self.coal_production = int(csvData['Coal Production']) if csvData['Coal Production'] else 0
        self.iron_production = int(csvData['Iron Production']) if csvData['Iron Production'] else 0
        self.beer_production_canal = int(csvData['Beer Production Canal']) if csvData['Beer Production Canal'] else 0
        self.beer_production_rail = int(csvData['Beer Production Rail']) if csvData['Beer Production Rail'] else 0
        self.points = int(csvData['Points']) if csvData['Points'] else 0
        self.income_levels = int(csvData['Income Levels']) if csvData['Income Levels'] else 0
        self.links = int(csvData['Links']) if csvData['Links'] else 0
        #Calculate the cost list based on the coal, iron, and beer costs
        self.cost_list = sorted(["Coal"]*self.coal_cost + ["Iron"]*self.iron_cost)
    
    def compare_cost_list(self, cost_list: list) -> bool:
        # Compare the cost list of the industry with the given cost list, ignoring order
        return sorted(cost_list) == self.cost_list

class Game_Properties:
    def __init__(self):
        # Create a dict of Industry_Properties based on industry_data and 
        self.industry_dict = {key:Industry_Properties(key, data) for key, data in industry_data.items()}
        self.industry_layout = {"Crate": [None]*11, "Shed": [None]*11, "Pottery": [None]*5, "Beer": [None]*7, "Iron": [None]*4, "Coal": [None]*7}
        for _, industry_tile in self.industry_dict.items():
            #Sizes of the board lists have been pre-allocated, so this should perform without error, if there is an error, then good because we caught something
            self.industry_layout[industry_tile.industry][industry_tile.sequence] = industry_tile
        # Create the income level to income mapping list
        self.income_level_to_income = []
        self.income_level_to_income.append([i for i in range(-10,1)])  # Level 0-10
        self.income_level_to_income.extend([i for i in range(1, 12) for _ in range(2)])
        # Setup the market return values
        self.coal_market_cost = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8]
        self.iron_market_cost = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6]
        # Setup parameters
        self.starting_money = 36 #Rules say 17

class Player:
    def __init__(self, player_id, player_color, game_properties: Game_Properties):
        #Set attributes
        self.game_properties = game_properties
        self.money = game_properties.starting_money #Starting money for each player
        self.player_id = player_id
        self.player_color = player_color
        self.points = 0
        self.income_level = 0
        self.hand = [] #Not yet used, concept of cards not planned to be implemented in this simulation
        self.discard = []
        self.industry_next = {"Crate": 0, "Shed": 0, "Pottery": 0, "Beer": 0, "Iron": 0, "Coal": 0}
    
    def copy(self):
        this = copy.copy(self)
        this.hand = self.hand[:]
        this.discard = self.discard[:]
        this.industry_next = self.industry_next.copy()
        return this
    
    def string_print(self):
        # Return a string representation of the player
        industry_next_str = str([self.game_properties.industry_layout[industry][sequence].name for industry, sequence in self.industry_next.items()]).replace("'", "").replace(",", "")
        s = f"Player {self.player_id} ({self.player_color}): Money: {self.money}, Points: {self.points}, Income Level: {self.income_level}, Industry Next: {industry_next_str}"
        return s
      
    def build_tile(self, industry_name, controller: Action_Controller) -> Industry_Properties | str:
        #Build a tile of the specified industry type, return an industry
        #Or throw an error if the industry cannot be built
        built_tile = self.game_properties.industry_dict[industry_name]
        #Check if the industry is the next to be built
        if built_tile.sequence != self.industry_next[built_tile.industry]:
            return controller.test(f"Invalid action: Player {self.player_id} cannot build {built_tile.name} at this time.")
        #Increase the industry next to be built
        self.industry_next[built_tile.industry] += 1
        controller.record(self, built_tile.industry, delta = 1)
        #Spend the money to build the industry
        if (r := self.delta_money(-1*built_tile.money_cost, controller=controller)): return r
        #All player checks have been passed, return the played industry
        return built_tile

    def develop_tile(self, industry_name, controller: Action_Controller):
        #Develop a tile by the name of the industry, coal will be spent elsewhere
        built_tile = self.game_properties.industry_dict[industry_name]
        #Check if the industry is the next to be built
        if built_tile.sequence != self.industry_next[built_tile.industry]:
            return controller.test(f"Invalid action: Player {self.player_id} cannot build {built_tile.name} at this time.")
        #Increase the industry next to be built
        self.industry_next[built_tile.industry] += 1
        controller.record(self, built_tile.industry, delta = 1)
        #Check if the industry cannot be developed because development_restriction is True
        if built_tile.development_restriction:
            return controller.test(f"Invalid action: Player {self.player_id} cannot develop {built_tile.name} at this time.")

    def award_points(self, points: int, controller: Action_Controller):
        #Award points to the player
        self.points += points
        controller.record(self, "points", delta = points)
        #Set minimum points to 0
        if self.points < 0:
            self.points = 0

    def award_income_levels(self, income_level: int, controller: Action_Controller):
        #Award income to the player
        self.income_level += income_level
        controller.record(self, "income_level", delta = income_level)
        #Restrain income level from 0 to 99
        if self.income_level < 0:   
            return controller.test(f"Invalid action: Player {self.player_id} cannot have negative income level.")
        elif self.income_level > 99:
            self.income_level = 99

    def delta_money(self, delta: int, controller: Action_Controller):
        #Change the money of the player
        self.money += delta
        controller.record(self, "money", delta = delta)
        #Error if money is negative
        if self.money < 0:
            return controller.test(f"Invalid action: Player {self.player_id} cannot have negative money.")

    def loan(self, controller: Action_Controller):
        #Take a loan of 30 money and move down 3 income levels
        if (r := self.delta_money(30, controller)): return r
        if (r := self.award_income_levels(-3, controller)): return r
    
    def get_build_options(self) -> list[Industry_Properties]:
        # Get a list of industry names that can be built by the player
        build_options = []
        for industry, sequence in self.industry_next.items():
            if sequence < len(self.game_properties.industry_layout[industry]):
                industry_tile = self.game_properties.industry_layout[industry][sequence]
                build_options.append(industry_tile)
        return build_options

class Played_Industry:
    def __init__(self, player: Player, industry_properties: Industry_Properties, age: str):
        self.player = player
        self.properties = industry_properties
        #Setup the state of the played industry when played
        self.flipped = False
        #Setup resources remaining for the industry to be removed
        self.resource_remaining = industry_properties.coal_production + industry_properties.iron_production + \
                (industry_properties.beer_production_canal if age == "canal" else industry_properties.beer_production_rail)
        
    def string_print(self):
        # Return a string representation of the played industry
        s = f"{self.properties.name}-P{self.player.player_id}-{"F" if self.flipped else "U" + str(self.resource_remaining + self.properties.beer_cost)}"
        return s

    def spend_resource(self, controller: Action_Controller):
        #Spend a resource from the industry, return the resource spent
        #Check if the industry is flipped
        if self.flipped:
            return controller.test(f"Invalid action: Player {self.player.player_id} cannot spend a resource from {self.properties.name} at this time.")
        #Check if the industry has any resources remaining
        if self.resource_remaining <= 0:
            return controller.test(f"Invalid action: Player {self.player.player_id} cannot spend a resource from {self.properties.name} at this time.")
        #Spend a resource from the industry
        self.resource_remaining -= 1
        controller.record(self, "resource", delta = -1)
        #Check if the industry has 0 resources remaining and should therefore be flipped
        if self.resource_remaining == 0:
            self.flipped = True
            controller.record(self, "flipped", new_value = True)
            #Award the player points for the industry and income for the industry
            if (r := self.player.award_points(self.properties.points, controller)): return r
            if (r := self.player.award_income_levels(self.properties.income_levels, controller)): return r

    def sell(self, controller: Action_Controller):
        #Sell the resource from the industry and flip. Beer cost will be handled in the game state
        #Check to ensure the industry is type Manufactured
        if self.properties.industry_type != "Manufactured":
            return controller.test(f"Invalid action: Player {self.player.player_id} cannot sell a resource from {self.properties.name} at this time.")
        #Check if the industry is flipped
        if self.flipped:
            return controller.test(f"Invalid action: Player {self.player.player_id} cannot sell a resource from {self.properties.name} at this time.")
        self.flipped = True
        controller.record(self, "flipped", new_value = True)
        #Award the player points for the industry and income for the industry
        if (r := self.player.award_points(self.properties.points, controller)): return r
        if (r := self.player.award_income_levels(self.properties.income_levels, controller)): return r

    def copy(self):
        # Copy the played industry to a new object (shallow copy)
        return copy.copy(self)


#main_actions: typing.Literal["build", "network", "develop", "sell", "loan", "scout", "pass"]
"""
card_play.player_id.main_action.using_card:main_action_1<resources>;main_action_2<resources>;...
    <resources> as <location_1,location_2,...>
    Individual actions are separated by spaces
    The main actions are formatted as follows:
        build.card:industry_tile_name.location_built<resources> #Needs to account for overbuilding (which I think this does by specifying a location that is already used)
        network.card:from_location.to_location<resources>;from_location.to_location<resources> #Second paramter used if a second link is built using the same action
        develop.card:industry_tile_name<resources>;industry_tile_name<resources> #Second paramter used if a second tile is developed
        sell.card:industry_tile_name.sale_location<resources>;industry_tile_name<resources>;etc. #Multiple sections used if multiple resources are sold
        loan.card: #No parameters needed for loans
        scout.card:discard_1;discard_2 #specifies the additional cards discarded
        pass.card: #No parameters needed for passing
    Standard parameters
        card_play as integer (the card number played within the game
        player_id as integet (the player_id of the current action player)
        card as "CrateBox0", "Birmingham1", "WildLocation0", "Unknown" #Unknown will be used while cards are not defined
        industry_tile_name as "Crate0", "Pottery2"
        location as
            @ specifies a city on the map of the form "@Birmingham1", "@Coventry2", "@Unknown0" #with @Unknown0 used until a real map is built out
            $ specifies a market location of the form $Iron04, $Coal12
            & specifies a sales location of the form &Oxford1, &Oxford2, &Unknown0 #with &Unknown0 used until a real map is built out
"""

class Action_Argument:
    def __init__(self, argument_string:str, resources:list):
        # Initialize the action argument with its components
        # Argument string and resources must always be present, if no resources are required, then resources will be an empty list
        self.argument_string = argument_string
        self.resources = resources
        self.tile: str
        self.location: str
        self.from_location: str
        self.to_location: str
        self.cards: str
    def make_resource_string(self, resource_list) -> str:
        # Create a string representation of the resources
        if resource_list:
            return f"<{','.join(resource_list)}>"
        else:
            return ""

# Build an action argment for each main action type, from components, creates the string for the action argument
class Action_Argument_Build(Action_Argument):
    def __init__(self, tile_name: str, location: str, resources: list):
        # Initialize the action argument with its components
        self.tile = tile_name
        self.location = location
        super().__init__(f"{tile_name}.{location}{self.make_resource_string(resources)}", resources)
class Action_Argument_Network(Action_Argument):
    def __init__(self, from_location: str, to_location: str, resources: list):
        # Initialize the action argument with its components
        self.from_location = from_location
        self.to_location = to_location
        super().__init__(f"{from_location}.{to_location}{self.make_resource_string(resources)}", resources)
class Action_Argument_Develop(Action_Argument):
    def __init__(self, tile_name: str, resources: list):
        self.tile = tile_name
        # Initialize the action argument with its components
        super().__init__(f"{tile_name}{self.make_resource_string(resources)}", resources)
class Action_Argument_Sell(Action_Argument):
    def __init__(self, tile_name: str, location: str, resources: list):
        self.tile = tile_name
        self.location = location
        super().__init__(f"{tile_name}.{location}{self.make_resource_string(resources)}", resources)
# class Action_Argument_Loan(Action_Argument):
#     def __init__(self):
#         # Initialize the action argument with its components
#         super().__init__("", [])
class Action_Argument_Scout(Action_Argument):
    def __init__(self, card: str):
        # Initialize the action argument with its components
        self.card = card
        super().__init__(f"{card}", [])
# class Action_Argument_Pass(Action_Argument):
#     def __init__(self):
#         # Initialize the action argument with its components
#         super().__init__("", [])

def parse_action_argment_string(argument_string: str, main_action: str) -> Action_Argument:
    # Split the argument string into its components
    if "<" in argument_string:
        argument_left, resource_list = argument_string.replace(">", "").split("<")
        resource_list = resource_list.split(",")
    else:
        argument_left = argument_string
        resource_list = []
    #Make dictionaries by argument type
    if main_action == "build":
        tile, location = argument_left.split(".")
        return Action_Argument_Build(tile, location, resource_list)
    elif main_action == "network":
        from_location, to_location = argument_left.split(".")
        return Action_Argument_Network(from_location, to_location, resource_list)
    elif main_action == "develop":
        tile = argument_left
        return Action_Argument_Develop(tile, resource_list)
    elif main_action == "sell":
        tile, location = argument_left.split(".")
        return Action_Argument_Sell(tile, location, resource_list)
    elif main_action == "loan":
        raise ValueError(f"Invalid action argument: {argument_string}")
    elif main_action == "scout":
        card = argument_left
        return Action_Argument_Scout(card)
    elif main_action == "pass":
        raise ValueError(f"Invalid action argument: {argument_string}")
    else:
        raise ValueError(f"Invalid action argument: {argument_string}")

class Action:
    def __init__(self, card_play:int, player_id:int, card: str, main_action: str, action_arguments_list: list[Action_Argument]):
        # Initialize the action with its components
        self.card_play = card_play
        self.player_id = player_id
        self.used_card = card
        self.main_action = main_action
        self.arguments = action_arguments_list
        self.action_string = action_string
        self.action_string = f"{card_play}.{player_id}.{main_action}.{card}:{';'.join([arg.argument_string for arg in action_arguments_list])}"

def parse_action_string(action_string: str) -> Action:
    # Parse the action string into an Action object
    left_side, right_side = action_string.split(":")  # separation left to right
    card_play, player_id, main_action, used_card = left_side.split(".")
    action_arguments_list = []
    for argument_string in right_side.split(";"):
        if argument_string == "":
            # Skip empty arguments
            continue
        # Parse the argument string
        action_arguments_list.append(parse_action_argment_string(argument_string, main_action))
    return Action(card_play=int(card_play), player_id=int(player_id), card=used_card, main_action=main_action, action_arguments_list=action_arguments_list)

class Action_Parsed:
    def __init__(self, action_string: str):
        self.action_string = action_string
        left_side, right_side = action_string.split(":") #separation left to right
        card_play, player_id, self.main_action, self.used_card = left_side.split(".")
        self.card_play = int(card_play)
        self.player_id = int(player_id)
        self.argument_strings = right_side.split(";")
        self.arguments: list[Action_Argument] = []
        for argument_string in self.argument_strings:
            if argument_string == "":
                # Skip empty arguments
                continue
            # Parse the argument string
            self.arguments.append(parse_action_argment_string(argument_string, self.main_action))

class Game_State():
    def __init__(self):
        # Sets up a new game
        self.properties = Game_Properties()
        self.players = [Player(0, "red", self.properties)]
        self.age = "canal"
        self.round = 0 #index from 0
        self.card_play = 0  #index from 0, card play is the total number of card plays in the game
        self.active_player_index = 0
        self.active_player_card = 1  # The card that the active player is currently playing, index from 0
        self.coal_market_last_filled = 1
        self.iron_market_last_filled = 2
        self.played_industries: list[Played_Industry] = []
        self.played_links = []
        #Setup lineage, these parameters are set when using the copy method and take action method
        self.parent: Game_State = None  # Reference to the parent game state, used for tree traversal
        self.previous_action: Action = None  # The action that led to this game state, used for tree traversal
    
    def copy(self):
        #Copy self to a new object (shallow copy)
        this = copy.copy(self)
        this.players = [player.copy() for player in self.players]
        this.played_industries = [industry.copy() for industry in self.played_industries]
        this.played_links = self.played_links[:]
        # Sets the lineage attributes
        this.parent = self  # Keep the parent reference
        this.previous_action = None # Reset the previous action for the copied state
        return this
    
    def string_print(self, action_history_flag: bool = False) -> str:
        # Return a string representation of the game state
        s = f"Game State: (Previous action: {self.previous_action.action_string if self.previous_action else 'None'})" + \
            f"\n  Round: {self.round}, Card Play: {self.card_play}, Age: {self.age}, Active Player: {self.active_player_index}" + \
            f"\n  Coal Market Last Filled: {self.coal_market_last_filled}, Iron Market Last Filled: {self.iron_market_last_filled}" + \
            f"\n  Played Links: {self.played_links}" + \
            f"\n  Played Industries: {str([played_industry.string_print() for played_industry in self.played_industries]).replace("'","")[1:-1]}" + \
            f"\n  Players:"
        for player in self.players:
            s += f"\n    {player.string_print()}"
        # Print the action history
        if action_history_flag:
            s += f"\n  Action History: {"None" if self.previous_action is None else ""}"
            game = self
            while game.parent is not None:
                s += f"\n    {"None" if game.previous_action is None else game.previous_action.action_string}"
                game = game.parent
        #Return the completed string
        return s

    def take_action_copy(self, action:Action, controller: Action_Controller) -> tuple["Game_State", str]:
        # Take an action returning a COPY of the game_state
        game = self.copy()  # Create a copy of the game state to modify
        # Check if the action is valid and perform it
        return_string = game._take_action_self(action, controller)
        return game, return_string

    def _take_action_self(self, action: Action, controller: Action_Controller) -> str:
        # Take an action modifying the game state in place -- Really should not be used
        # Test if the main action should be recorded in the controller
        controller.start_main_action(action = action, game = self)
        #The the action specified by the action string, otherwise an error message will be thrown
        self.previous_action = action  # Set the previous action for lineage tracking
        if action.player_id != self.players[self.active_player_index].player_id:
            return controller.test(f"Invalid action: Player {action.player_id} cannot take action during Player {self.players[self.active_player_index].player_id}'s turn.")
        active_player = self.players[self.active_player_index]
        # Perform the action based on the parsed arguments
        if action.main_action == "build":
            #Have the player remove the tile from their board spending money
            built_tile = active_player.build_tile(action.arguments[0].tile, controller=controller)
            if isinstance(built_tile, str): return built_tile #There was an error in building the tile
            # Check if the tile can't be built due to age restrictions
            if built_tile.age_restriction and built_tile.age_restriction != self.age:
                return controller.test(f"Invalid action: Player {action.player_id} cannot build {built_tile.name} at this time.")
            # Spend the resources to build the industry
            if (r := self.spend_resources(build_location=action.arguments[0].location, resource_locations=action.arguments[0].resources,
                                            required_resources=built_tile.cost_list, active_player=active_player, controller=controller)):
                return r
            # Create a new played industry and add it to the list of played industries
            played_industry = Played_Industry(active_player, built_tile, self.age)
            self.played_industries.append(played_industry)
            controller.record(self, "played_industry", new_value = built_tile.name)
            # Sell excess resources from the played industry to the market
            if built_tile.industry == "Coal":
                while played_industry.resource_remaining > 0 and self.coal_market_last_filled > 0:
                    # Spend the resource to the market & award the player money
                    if (r := played_industry.spend_resource(controller=controller)): return r
                    self.coal_market_last_filled -= 1
                    controller.record(self, "coal_market_last_filled", delta = -1)
                    if (r := active_player.delta_money(self.properties.coal_market_cost[self.coal_market_last_filled], controller=controller)): return r
            elif built_tile.industry == "Iron":
                while played_industry.resource_remaining > 0 and self.iron_market_last_filled > 0:
                    # Spend the resource to the market & award the player money
                    if (r := played_industry.spend_resource(controller=controller)): return r
                    self.iron_market_last_filled -= 1
                    controller.record(self, "iron_market_last_filled", delta = -1)
                    if (r := active_player.delta_money(self.properties.iron_market_cost[self.iron_market_last_filled], controller=controller)): return r
            # Build action complete
        elif action.main_action == "network":
            if self.age == "canal":
                #Build a canal link at the cost of 3 money
                if (r := active_player.delta_money(-3, controller=controller)): return r
            if self.age == "rail":
                if len(action.arguments) == 1:
                    #Build a rail link at the cost of 5 money and one coal
                    if (r := active_player.delta_money(-5, controller=controller)): return r
                    if (r := self.spend_resources("Unknown", ["Coal"], ["Coal"], active_player, controller=controller)): return r
                elif len(action.arguments) == 2:
                    #Build a rail link at the cost of 15 money, 1 coal for first link, and 1 coal + 1 beer for the second link
                    if (r := active_player.delta_money(-15, controller=controller)): return r
                    if (r := self.spend_resources("Unknown", ["Coal"], ["Coal"], active_player, controller=controller)): return r
                    if (r := self.spend_resources("Unknown", ["Coal", "Beer"], ["Coal", "Beer"], active_player, controller=controller)): return r
                else:
                    return controller.test(f"Invalid action: Player {action.player_id} cannot build a rail link at this time.")
            # Place the link in the played links list
            self.played_links.append("Unknown") # Placeholder for the link, should be replaced with the actual link object
            controller.record(self, "played_link", new_value = "Unknown")
        elif action.main_action == "develop":
            for argument in action.arguments:
                if (r := active_player.develop_tile(argument.tile, controller=controller)): return r
                if (r := game.spend_resources("Unknown", argument.resources, ["Iron"], active_player, controller=controller)): return r
        elif action.main_action == "sell":
            tile_name = action.arguments[0].tile
            # Find the played industry with the specified tile name
            played_industry = next((industry for industry in self.played_industries if industry.properties.name == tile_name), None)
            if played_industry is None:
                return controller.test(f"Invalid action: Player {action.player_id} cannot sell a resource from {tile_name} at this time.")
            # Sell the good from the played industry
            played_industry.sell(controller=controller)
            # Consume the appropriate amount of beer
            if (r := self.spend_resources("Unknown", ["Beer"]*played_industry.properties.beer_cost, ["Beer"]*played_industry.properties.beer_cost, active_player, controller=controller)): return r
            #This should complete the sell action
        elif action.main_action == "loan":
            active_player.loan(controller=controller)
        elif action.main_action == "scout":
            #Raise an error as scouting is not yet implemented
            return controller.test(f"Invalid action: Player {action.player_id} cannot scout at this time.")
        elif action.main_action == "pass":
            #Raise an error as passing is not yet implemented
            return controller.test(f"Invalid action: Player {action.player_id} cannot pass at this time.")
        else:
            return controller.test(f"Invalid action: {action.main_action} is not a valid action.")
        # The action was successful, so we can move to the next card play
        self.increment_card_play()
        # Have the controller record end of the action
        controller.end_main_action(game = self)
        # Action was successful, retuurn a blank string
        return ""
    
    def increment_card_play(self):
        self.card_play += 1
        self.active_player_card += 1
        #Every other card, move to the next player
        if self.active_player_card >= 2:
            self.active_player_index += 1
            #If the active player card is in a skipped round, start with active player card of 1
            if self.card_play < len(self.players):
                self.active_player_card = 1
            else:
                self.active_player_card = 0
        #If the active player is greater than last player, move to the next round
        if self.active_player_index >= len(self.players):
            self.active_player_index = 0
            self.round += 1

    def spend_resources(self, build_location: str, resource_locations: list, required_resources: list, active_player: Player, controller: Action_Controller):
        # This function is used to check if the resources spent are valid and flips tiles as needed
        # Return a list of the resources spent
        spent_resources = []
        for resource_needed in resource_locations:
            # For now, the locations will only be "Coal", "Iron", "Beer"
            # And will take the resource from the first avaliable location for simplicity
            for industry in self.played_industries:
                if industry.properties.industry == resource_needed and industry.resource_remaining > 0:
                    if (r := industry.spend_resource(controller=controller)): return r
                    spent_resources.append(resource_needed)
                    break
            else:
                #Played industy was not found from which resource could be spent
                #Buy resources from the market
                if resource_needed == "Coal":
                    cost = self.properties.coal_market_cost[self.coal_market_last_filled]
                    self.coal_market_last_filled = min(self.coal_market_last_filled + 1, len(self.properties.coal_market_cost) - 1)
                    controller.record(self, "coal_market_last_filled", delta = 1)
                elif resource_needed == "Iron":
                    cost = self.properties.iron_market_cost[self.iron_market_last_filled]
                    self.iron_market_last_filled = min(self.iron_market_last_filled + 1, len(self.properties.iron_market_cost) - 1)
                    controller.record(self, "iron_market_last_filled", delta = 1)
                else:
                    return controller.test(f"Invalid action: Player {active_player.player_id} cannot buy {resource_needed} at this time.")
                #Was able to buy the resource
                spent_resources.append(resource_needed)
                #Spend the player's money
                if (r := active_player.delta_money(-1*cost, controller=controller)): return r
        #Check if the resources spent are the correct resources and amounts
        if sorted(spent_resources) != sorted(required_resources):
            return controller.test(f"Invalid action: Player {active_player.player_id} spent {spent_resources} but was supposed to spend {required_resources}.")
        # Resources were spent successfully, return

    def get_untested_actions(self) -> list[Action]:
        # Returns a list of possible actions that have not been tested yet, leave it up to other processes to determine if the action is valid
        untested_actions = []
        # Possible build actions
        for industry_properties in self.players[self.active_player_index].get_build_options():
            action = Action(
                card_play=self.card_play,
                player_id=self.active_player_index,
                card="Unknown",  # Placeholder for the card, should be replaced with the actual card object
                main_action="build",
                action_arguments_list=[Action_Argument_Build(industry_properties.name, "@Unknown0", industry_properties.cost_list)]
            )
            untested_actions.append(action)
        # Loan action
        untested_actions.append(Action(
            card_play=self.card_play,
            player_id=self.active_player_index,
            card="card",  # Placeholder for the card, should be replaced with the actual card object
            main_action="loan",
            action_arguments_list=[]
        ))
        # Sell actions -- start with only allowing a single sale
        for industry in self.played_industries:
            if industry.properties.industry_type == "Manufactured" and not industry.flipped:
                action = Action(
                    card_play=self.card_play,
                    player_id=self.active_player_index,
                    card="Unknown",  # Placeholder for the card, should be replaced with the actual card object
                    main_action="sell",
                    action_arguments_list=[Action_Argument_Sell(tile_name=industry.properties.name, location="$Unknown0", resources=["Beer"]*industry.properties.beer_cost)]
                )
                untested_actions.append(action)
        return untested_actions


class Supervisor:
    # This class is used to setup the genetic algorythm to run copies of the game state and determine the best actions to take
    # For each game in .games, a randomized subset of the games weighted by how good the outcomes are, will be selected to survive to the next generation
    # The surviving games will be pruned back and random moves will be taken from the pruned point to make new games in the population=
    def __init__(self):
        self.games: list[Game_State] = []
        self.games.append(Game_State())  # Start with a single game state

    def prune_and_complete(self, game: Game_State):
        # Take a random previous state of the game, based on the number of card plays, trace back through parents
        # For that previous state, complete the game using the complete_game function
        i = random.randint(0, game.card_play - 1)  # Choose a random card play to trace back to
        pruned_game = game.get_state_at_card_play(i)
        new_game = self.complete_game(pruned_game)
        return new_game

    def complete_game(self, game: Game_State, controller: Action_Controller):
        # This function will call decide_and_perform_action until the game is complete
        # Record starting state if valid
        controller.start_game_completion(game=game)
        # Complete the game by performing actions until the game is complete
        while game.round < 8:
            game = self.decide_and_perform_action(game, controller=controller)
        return game
    
    def decide_and_perform_action(self, game: Game_State, controller: Action_Controller) -> Game_State:
        # Get the valid children of the game, choose one at random, and return the new game state
        # Setup selection 
        valid_children = self.get_valid_children(game, controller=controller.sub_controller)
        if not valid_children:
            raise ValueError("No valid children found for the game state.")
        # Choose a random child game state
        chosen_child = random.choice(valid_children)
        controller.next_game_completion(chosen_child=chosen_child, valid_children=valid_children)
        # Set parent lineage
        return chosen_child

    def get_valid_children(self, game: Game_State, controller: Action_Controller) -> list[Game_State]:
        # Called to take a turn in a game
        # Evaluates each possible action, for the successful actions, it will return a new game state with the action applied
        valid_children = []
        for action in game.get_untested_actions():
            new_game_state, return_string = game.take_action_copy(action, controller)
            if not return_string:
                valid_children.append(new_game_state)
        return valid_children


# Example action strings
partial_action_string = [
    "build.card:Crate0.@Birmingham1<Coal>",
    "build.card:Coal0.@Birmingham1",
    "develop.card:Beer0<Iron>;Beer1<Iron>",
    "build.card:Beer2.@Birmingham1<Iron>",
    #"sell.card:Crate0.$Location0<Beer>"
]
game = Game_State()
main_controller = Action_Controller(record=True, verbose=False, test_mode=False)
for action_string in partial_action_string:
    action_string = f"{game.card_play}.{game.active_player_index}.{action_string}"
    action = Action_Parsed(action_string)
    game, return_string = game.take_action_copy(action, main_controller)

print()
print("----------------------------------------------------")
print()
supervisor = Supervisor()
main_controller = Action_Controller(record=True, verbose=True, test_mode=False)
q = supervisor.complete_game(game, main_controller)