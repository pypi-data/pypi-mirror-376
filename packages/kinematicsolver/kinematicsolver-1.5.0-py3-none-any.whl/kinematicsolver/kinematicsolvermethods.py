import math
def KinematicSolverUAM(SUVAT):
    newSUVAT = SUVAT.copy()
    if SUVAT[0] == None:
        if SUVAT[1] is not None and SUVAT[3] is not None and SUVAT[4] is not None:
            newSUVAT[0] = SUVAT[1]*SUVAT[4]+(1/2)*SUVAT[3]*SUVAT[4]*SUVAT[4]
        else:
            if SUVAT[3] == 0:
                newSUVAT[0] = SUVAT[1]*SUVAT[4]
            else:
                newSUVAT[0] = ((SUVAT[2]*SUVAT[2])-(SUVAT[1]*SUVAT[1]))/(2*SUVAT[3])
    if SUVAT[1] is None:
        if SUVAT[2] is not None and SUVAT[3] is not None and SUVAT[4] is not None:
            newSUVAT[1] = SUVAT[2] - SUVAT[3] * SUVAT[4]
        elif SUVAT[2] is None:
            newSUVAT[1] = (newSUVAT[0] - (1/2)*SUVAT[3]*SUVAT[4]*SUVAT[4])/SUVAT[4]
        elif SUVAT[4] is None:
            newSUVAT[1] = (SUVAT[2]*SUVAT[2])-(2*SUVAT[3]*newSUVAT[0])
            newSUVAT[1] = math.sqrt(newSUVAT[1])
    if SUVAT[2] is None:
        if SUVAT[1] is not None and SUVAT[3] is not None and SUVAT[4] is not None:
            newSUVAT[2]= newSUVAT[1]+SUVAT[3]*SUVAT[4]
        elif SUVAT[4] is None:
            newSUVAT[2] = newSUVAT[1]*newSUVAT[1]+ 2* SUVAT[3] * SUVAT[0]
            newSUVAT[2] = math.sqrt(newSUVAT[2])
    if SUVAT[3] is None:
        if SUVAT[1] is not None and SUVAT[2] is not None and SUVAT[4] is not None:
            newSUVAT[3] = (newSUVAT[2]-newSUVAT[1])/SUVAT[4]
        elif SUVAT[2] is None:
            newSUVAT[3] = (newSUVAT[0] - (SUVAT[4]*newSUVAT[1]))/((1*SUVAT[4]*SUVAT[4])/2)
        else:
            newSUVAT[3] = ((newSUVAT[2]*newSUVAT[2])-(newSUVAT[1]*newSUVAT[1]))/(2*newSUVAT[0])
    if SUVAT[4] is None:
        if SUVAT[1] is not None and SUVAT[2] is not None and SUVAT[3] is not None:
            newSUVAT[4] = (newSUVAT[2]-newSUVAT[1])/ newSUVAT[3]
        else:
            if newSUVAT[3] == 0:
                newSUVAT[4] = newSUVAT[0]/newSUVAT[1]
            else:
                t1 = (-newSUVAT[1] + math.sqrt((newSUVAT[1]*newSUVAT[1])+2*newSUVAT[3]*newSUVAT[0]))/newSUVAT[3]
                t2 = (-newSUVAT[1] - math.sqrt((newSUVAT[1]*newSUVAT[1])+2*newSUVAT[3]*newSUVAT[0]))/newSUVAT[3]
                if t1>=t2:
                    newSUVAT[4] = t1
                else:
                    newSUVAT[4] = t2
    return newSUVAT