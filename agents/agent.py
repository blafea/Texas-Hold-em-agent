import random
from game.engine.hand_evaluator import HandEvaluator
from game.engine.card import Card
from game.players import BasePokerPlayer

def pick_unused_card(card_num, used_card):
    used = [card.to_id() for card in used_card]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]
    choiced = random.sample(unused, card_num)
    return [Card.from_id(card_id) for card_id in choiced]

def montecarlo_simulation(hole_card, community_card):
    need_num = 5 - len(community_card)
    community_card = community_card + pick_unused_card(need_num, hole_card+community_card)
    opponents_hole = pick_unused_card(2, hole_card + community_card)
    opponents_score = HandEvaluator.eval_hand(opponents_hole, community_card)
    my_score = HandEvaluator.eval_hand(hole_card, community_card)
    return 1 if my_score >= opponents_score else 0

def estimate_win_rate(simulation_times, hole_card, community_card=None):
    if not community_card: community_card = []
    win_count = sum([montecarlo_simulation(hole_card, community_card) for _ in range(simulation_times)])
    return 1.0 * win_count / simulation_times

Simulation_Times = 1000
class MonteCarloPlayer(BasePokerPlayer):
    def __init__(self):
        super().__init__()

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [fold_action_info, call_action_info, raise_action_info]
        community_card = round_state['community_card']
        win_rate = estimate_win_rate(
            simulation_times=Simulation_Times,
            hole_card=[Card.from_str(s) for s in hole_card],
            community_card=[Card.from_str(s) for s in community_card]
        )

        #print(hole_card)
        #print(round_state)
        stack = round_state['seats'][1]['stack']
        for his in round_state['action_histories'].values():
            for op in his:
                if op['uuid'] == self.uuid:
                    stack += op['amount']
        min_max = [op for op in valid_actions if op['action'] == 'raise'][0]['amount']
        max = min_max['max']
        min = min_max['min']
        call_amount = [item for item in valid_actions if item['action'] == 'call'][0]['amount']
        try:
            opponent_action = round_state['action_histories'][round_state['street']][-1]['action']
        except:
            if round_state['street'] == 'turn':
                opponent_action = round_state['action_histories']['flop'][-1]['action']
            else:
                opponent_action = round_state['action_histories']['preflop'][-1]['action']

        if stack > 1000 + (20 - round_state['round_count'])*10:
            action = 'fold'
            amount = 0
        elif round_state['street'] == 'preflop':
            if opponent_action == 'RAISE' or win_rate < 0.4:
                action = 'fold'
                amount = 0
            else:
                action = 'call'
                amount = call_amount
        elif round_state['street'] == 'river' and opponent_action != 'RAISE':
            action = 'call'
            amount = call_amount
        elif round_state['round_count'] > 7 and stack < 1100 and stack > 900:
            if opponent_action == 'RAISE':
                action = 'fold'
                amount = 0
            elif win_rate > 0.5:
                action = 'raise'
                amount = int((max - min) / 3 * 2 + min)
            else:
                action = 'call'
                amount = call_amount
        elif opponent_action == 'RAISE':
            if win_rate > 0.75:
                action = 'raise'
                amount = int((max - min) / 2 + min)
            elif win_rate > 0.6:
                action = 'call'
                amount = call_amount
            else:
                action = 'fold'
                amount = 0

        else:
            if win_rate > 0.75:
                action = 'raise'
                amount = int((max - min) / 2 + min)
            elif win_rate > 0.6:
                action = 'raise'
                amount = int((max - min) / 4 + min)
            elif win_rate > 0.5:
                action = 'call'
            else:
                num = random.uniform(0, 1)
                if num > 0.5:
                    action = 'call'
                    amount = call_amount
                else:
                    action = 'fold'
                    amount = 0


        return action, amount

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return MonteCarloPlayer()