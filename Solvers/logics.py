class TLogElement:
    def init(self):
        self.in1 = False
        self.__in2 = False
        self._res=False
        self.__nextEl = None
        self.__nextIn = 0
        if not hasattr (self, "calc"):
            raise NotImplementedError("Нельзя создать такой объект")
        
    def calc(self):
        pass

    def __setIn1 ( self, newIn1 ):
        self.__in1 = newIn1
        self.calc()
        if self.__nextEl:
            if self.__nextIn == 1:
                self.__nextEl.In1 = self._res
            elif self.__nextIn == 2:
                self.__nextEl.In2 = self._res
 
    def __setIn2(self, newIn2):
        self.__in2 = newIn2 
        self.calc()
        if self.__nextEl:
            if self.__nextIn == 1:
                self.__nextEl.In1 = self._res
            elif self.__nextIn == 2:
                self.__nextEl.In2 = self._res
    def link ( self, nextEl, nextIn ):
            self.__nextEl = nextEl
            self.__nextIn = nextIn

    In1 = property(lambda x: x.__in1, __setIn1)
    In2 = property(lambda x: x.__in2, __setIn2)
    Res=property(lambda x: x._res)    


class TNot ( TLogElement ):
    def __init (self):
        TLogElement.init(self)
    def calc (self):
        self._res = not self.In1


class TLog2In ( TLogElement ):
    pass


class TAnd ( TLog2In ):
    def init ( self ): 
        TLog2In.init ( self ) 
    def calc ( self ):
        self._res = self.In1 and self.In2


class TOr ( TLog2In ):
    def init ( self ): 
        TLog2In.init ( self ) 
    def calc ( self ):
        self._res = self.In1 or self.In2


class TXor(TLog2In):
    def init(self):
        super().init()
        self._and1 = TAnd()
        self._and2 = TAnd()
        self._not1 = TNot()
        self._not2 = TNot()
        self._or = TOr()
        
        self._not1.link(self._and2, 1)
        self._not2.link(self._and2, 2)
        self._and1.link(self._or, 1)
        self._and2.link(self._or, 2)
    def calc(self):
        self._and1.In1 = self.In1
        self._not2.In1 = self.In2
        self._and1.In2 = self._not2.Res
        
        self._not1.In1 = self.In1
        self._and2.In1 = self._not1.Res
        self._and2.In2 = self.In2
        
        self._or.In1 = self._and1.Res
        self._or.In2 = self._and2.Res
        
        self._res = self._or.Res


el_xor = TXor()


print("  A | B | A XOR B ")
print("-------------------")
for A in range(2):
    for B in range(2):
        el_xor.In1 = bool(A)
        el_xor.In2 = bool(B)
        print(" ", A, "|", B, "|", int(el_xor.Res))