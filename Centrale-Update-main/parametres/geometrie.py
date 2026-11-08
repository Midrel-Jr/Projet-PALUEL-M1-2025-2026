# volumes, sections, hauteurs, surfaces d'échanges
def géométrie():
    #coeur
    H_coeur = 4.27 #m #hauteur du coeur
    D_coeur = 3.5 #m #diamètre du coeur
    V_coeur = H_coeur * 3.14 * (D_coeur/2)**2 #m^3 #volume du coeur 
    A_coeur = 5000 #m^2 #surface d'échange des crayons

    #Cuve
    H_cuve = 13.6 #m #hauteur de la cuve
    D_cuve = 3.39 #m #diamètre de la cuve
    V_cuve = H_cuve * 3.14 * (D_cuve/2)**2 #m^3 #volume de la cuve
    

    #pressuriseur
    H_pr = 12 #m #hauteur du pressuriseur
    D_pr = 2.5 #m #diamètre du pressuriseur
    V_pr = H_pr * 3.14 * (D_pr/2)**2 #m^3 #volume du pressuriseur
    A_pr = 0.5 #m^2

    #Générateur de vapeur
    H_gv = 22.3 #m
    D_e_gv = 3.39 #m #Diamètre d'entré du gv
    V_gv = 350 #m^3
    A_gv = 6940 #m^2 #surface d'échange du générateur de vapeur

    #Pompes
    H_p = 5 #m
    D_p = 1.5 #m
    V_p = 15 #m^3 #volume de la pompe

    #Turbine Haute pression
    L_th = 10 #m
    D_rotor_th = 1.5 #m
    A_th = 80 #m^2 #surface d'échange de la turbine haute pression

    #Turbine Basse Pression
    L_tb = 15 #m
    D_rotor_tb = 4 #m
    A_tb = 2000 #m^2 #surface d'échange de la turbine basse pression

    #Condenseur
    L_cd = 15 #m #longueur du condenseur
    l_cd = 8 #m #largeur du condenseur
    h_cd = 8 #m #hauteur du condenseur
    V_cd = 1500 #m^3 #volume du condenseur
    A_cd = 40000 #m^2 #surface d'échange du condenseur
    
    return {"V_coeur": V_coeur, 
            "V_cuve": V_cuve, 
            "A_coeur": A_coeur, 
            "H_coeur": H_coeur, 
            "H_cuve": H_cuve, 
            "A_pr": A_pr, 
            "A_gv": A_gv, 
            "V_gv": V_gv, 
            "H_gv": H_gv, 
            "V_p": V_p, 
            "H_p": H_p, 
            "D_p": D_p, 
            "A_th": A_th, 
            "L_th": L_th, 
            "D_rotor_th": D_rotor_th, 
            "A_tb": A_tb, 
            "L_tb": L_tb, 
            "D_rotor_tb": D_rotor_tb, 
            "V_cd": V_cd, 
            "A_cd": A_cd, 
            "L_cd": L_cd, 
            "l_cd": l_cd, 
            "h_cd": h_cd
            }
print(géométrie())