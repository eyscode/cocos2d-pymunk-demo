__all__ = ['state']


class State(object):
    STATE_PAUSE, STATE_PLAY, STATE_WIN, STATE_OVER = range(4)

    def __init__( self ):
        # current score
        self.score = 0

        # time
        self.metros = 0

        # state
        self.state = self.STATE_PAUSE

    def reset( self ):
        self.score = 0
        self.metros = 0
        self.state = self.STATE_PAUSE

state = State()
