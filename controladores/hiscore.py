from modelos import constantes

__all__ = ['hiscore']

class HiScoreData(object):
    POINTS, NAME, LVL = range(3)

    HISCORE_FILENAME = 'hi_scores.txt'

    MAX = 7

    def __init__( self ):
        super(HiScoreData, self).__init__()
        self.load()

    def load(self):
        self.hi_scores = []
        try:
            f = open(self.HISCORE_FILENAME)
            for line in f.readlines():
                if line.startswith("#"):
                    continue
                (score, name, nada) = line.split(',')
                self.hi_scores.append((int(score), name ))
            f.close()
        except IOError, ex:
            pass

    def save(self):
        try:
            f = open(self.HISCORE_FILENAME, 'w')
            for i in self.hi_scores:
                f.write('%d,%s,\n' % ( i[0], i[1] ))
            f.close()
        except Exception, e:
            print 'Could not save hi scores'
            print e

    def add( self, score, name):
        for l in name:
            if not l.isalnum():
                name = name.replace(l, '_')
        self.hi_scores.append((int(score), name ))
        self.hi_scores.sort()
        self.hi_scores.reverse()
        self.hi_scores = self.hi_scores[:self.MAX]
        self.save()

    def is_in( self, score ):
        if len(self.hi_scores) < self.MAX:
            return True
        if score > self.hi_scores[-1][0]:
            return True
        return False

    def get( self, max=7 ):
        return self.hi_scores[:max]

hiscore = HiScoreData()
