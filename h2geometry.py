from toolkit import qnorm
import numpy as np


class H2Point:
    def __init__(self, z):
        self.z = z

class H2Segment:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def getCircleAndEndpoints(self):
        z1, z2 = self.p1.z, self.p2.z
        if (z2*np.conj(z1)).imag != 0.0:
            straight = False
            c = (z2*(1.0+qnorm(z1)) - z1*(1.0+qnorm(z2)))/(2.0*1j*(np.conj(z1)*z2).imag)
            r = np.sqrt(qnorm(c) - 1)
        else:
            straight = True
            c, r = -1, -1

        return straight, c, r, z1, z2


class H2Isometry:
    def __init__(self, u=1.0, a=0.0):
        self.u = u
        self.a = a
        if qnorm(a)>1 or abs(qnorm(u)-1)>0.001 :
            print("WARNING: Isometry not well-defined")

    def reset(self):
        self.u = 1.0
        self.a = 0.0

    def setByMappingPoint(self, pIn, pOut):
        z1, z2 = pIn.z, pOut.z
        n1, n2 = qnorm(z1), qnorm(z2)
        self.u = 1.0
        self.a = (z1*(1 - n2) - z2*(1 - n1)) / (1 - n1*n2)

    def __mul__(self, other):
        temp = 1.0 + self.a*np.conj(other.u*other.a)
        u = self.u*other.u*(temp*temp)/qnorm(temp)
        a = (other.a + (self.a*np.conj(other.u)))/temp
        return H2Isometry(u,a)

    def kick(self, p):
        zIn = p.z
        zOut = self.u*((zIn-self.a)/(1.0 - (np.conj(self.a)*zIn)))
        return H2Point(zOut)

    def kickSegment(self, s):
        return H2Segment(self.kick(s.p1), self.kick(s.p2))

    def inverse(self):
        u = np.conj(self.u)
        a = -self.u*self.a
        return H2Isometry(u, a)