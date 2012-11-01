class phameratorState:
  '''defines the possible states of the application'''
  def __init__(self):
    self.allowable_states = ['phages', 'phams', 'genes']
    self.busy = False
    self.state = None

  def change_state(self, new_state):
    '''called when switching the current state of the application'''
    self.state = state

class UiControlStateManager:
  '''show/hide or activate/inactivate menu items based on application state'''
  def __init__(self):
    self.allowable_widget_states = ['visible', 'invisible', 'sensitive', 'insensitive']
    '''keys are phamerator states, values are a dict with widget_state as key, widget as value''' 
    self.state_config = {}
    for s in phameratorState().allowable_states:
      self.state_config[s] = {}
  def register(self, phamerator_state, widget_state, widget):
    self.state_config[phamerator_state][widget_state] = widget
