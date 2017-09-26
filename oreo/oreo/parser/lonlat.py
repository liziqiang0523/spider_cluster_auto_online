#coding=utf-8

class lonlat:
  def getlonlat(self,ch):
    str2int = {'a':10,'b':11,'c':12,'d':13,'e':14,'f':15,'g':16,'h':17,'i':18,'j':19,'k':20,'l':21,'m':22,'n':23,'o':24,'p':25,'q':26,'r':27,'s':28,'t':29,'u':30,'v':31,'w':32,'x':33,'y':34,'z':35}
    int2str = {10:'a',11:'b',12:'c',13:'d',14:'e',15:'f',16:'g',17:'h',18:'i',19:'j',20:'k',21:'l',22:'m',23:'n',24:'o',25:'p',26:'q',27:'r',28:'s',29:'t',30:'u',31:'v',32:'w',33:'x',34:'y',35:'z'}
    add=10; plus=7; I = -1; H = 0; B = ""; J = len(ch) - 1; G = ord(ch[J]); C = ch[0:13]; temp = ch.lower();
    for s in range(J):
      D = str2int[temp[s:s+1]] - add
      if D >= add:
        D = D - plus
      if D < add:
        B += str(D)
      else:
        B += str(int2str[D])
      if D > H:
        I = s;
        H = D
    A = int(B[0:I],16)
    F = int(B[I + 1:I+7],16)
    L = (int(A) + int(F) - int(G)) / 2
    K = (float(F) - float(L)) / 100000
    L = float(L) / 100000
    return str(K),str(L)
