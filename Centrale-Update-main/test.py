'''N=int(input("Entrer la dimension de votre matrice"))
print("ligne  colonne")
i=1
compteur=0
while i<=N:
    j=i+1
    while j<=N:
        print(f"{i:^5d} {j:>5d}")
        compteur += 1
        j = j+1
    i = i+1
print("Taille de la matrice :", N, "x", N)
print("Nombre de cases parcourues :", compteur)'''

'''import random

puce=0
compteur=0
while puce<=5:
    puce = random.choice([1,-1])+puce
    compteur += 1
    print(puce)
print("le nombre de tours est ", compteur)'''

x0=0
x1=1
i=2
Fibonnaci = [x0, x1]
rapport = [0]
while i<15:
    Fibonnaci.append(Fibonnaci[i-1]+Fibonnaci[i-2])
    rapport.append(Fibonnaci[i]/Fibonnaci[i-1])
    i+=1
    print(Fibonnaci)
    print(rapport)
