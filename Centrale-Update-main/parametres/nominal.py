#débits, P, T, h en régime nominal
def nominal_primaire():
    #débits
    Q_p = 23325 #m^3/h #débit de fluide caloporteur dans une pompe primaire
    M_gv = 1909000 #kg/h 


    #pression
    P = 15500000 #Pa #pression dans le circuit primaire

    #Températures
    T_1ec = 565.95 #K #température d'entrée du fluide caloporteur dans le coeur
    T_1sc = 601.85 #K #température de sortie du fluide caloporteur du coeur

    #Puissance
    P_th = 3817e6 #W #puissance thermique du coeur
    P_cr = 17050 #W/m #puissance linéïque des crayons combustibles
    P_p = 5910 #kW #puissance de la pompe primaire
    
    #enthalpie
    
    return Q_p, M_gv, P, T_1ec, T_1sc, P_cr, P_p, P_th

def nominal_secondaire():
    #débits
    Q_vap_gv = 1909000 #kg/h #débit de vapeur dans le générateur de vapeur

    #pression
    P_gv = 6480000 #Pa #pression de sortie dans le générateur de vapeur
    P_turbine = 15500000 #Pa #pression dans la turbine #valeur à changer

    #Températures
    T_gv = 554.15 #K #température de sortie la vapeur dans le générateur de vapeur
    T_turbine = 601.85 #K #température de la vapeur dans la turbine

    return Q_vap_gv, P_gv, P_turbine, T_gv, T_turbine

def nominal_turbine():
    s = 0.05
    K_th = 0.215
    K_tb = 0.785
    T_th = 0.25*s
    T_tb = 0.25*s
    Kf = 0.005
    Kd = 0.85
    T_om_th = 0.5*s
    T_om_tb = 0.1*s
    N = 1500 #tr/min
    tau_p = 5 #s

    return K_th, K_tb, T_th, T_tb, Kf, Kd, s, T_om_th, T_om_tb, N, tau_p



print(nominal_primaire())
print(nominal_secondaire())
print(nominal_turbine())