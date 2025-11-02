import random
from dataclasses import dataclass


@dataclass
class Carta:
    valore: str
    seme: str
    forza_presa: int


# Gerarchia delle carte: valore nominale -> forza non briscola
forza_non_briscola = {
    "Asso": 90,
    "3": 80,
    "Re": 60,
    "Cavallo": 50,
    "Fante": 40,
    "7": 20,
    "6": 15,
    "5": 10,
    "4": 5,
    "2": 2,
}

# Forza di presa se la carta è briscola
forza_briscola = {
    "Asso": 100,
    "3": 95,
    "Re": 85,
    "Cavallo": 75,
    "Fante": 65,
    "7": 55,
    "6": 50,
    "5": 45,
    "4": 40,
    "2": 35,
}

semi = ["coppe", "denari", "spade", "bastoni"]
valori = ["Asso", "2", "3", "4", "5", "6", "7", "Fante", "Cavallo", "Re"]

mazzo_ordinato = [{"valore": valore, "seme": seme}
                  # Mazzo ordinato di carte napoletane
                  for valore in valori for seme in semi]
mazzo_mescolato = []  # Mazzo mescolato di carte da cui si estrarrà la briscola
mazzo_gioco = []  # Mazzo di gioco per le carte da distribuire

bussatori = []  # Lista per tenere traccia dei giocatori che bussano
affondatori = []  # Lista per tenere traccia dei giocatori che affondano


def mescola_mazzo():
    global mazzo_mescolato
    mazzo_mescolato = mazzo_ordinato.copy()
    random.shuffle(mazzo_mescolato)
    return mazzo_mescolato


def metti_briscola():
    # La prima carta del mazzo mescolato è la briscola
    briscola = mazzo_mescolato[0]
    # Rimuove la briscola dal mazzo
    mazzo_mescolato.pop(0)
    return briscola


def assegna_forza_presa(mazzo_mescolato, briscola):
    for carta in mazzo_mescolato:
        if carta["seme"] == briscola["seme"]:
            forza = forza_briscola[carta["valore"]]
            mazzo_gioco.append(
                Carta(valore=carta["valore"], seme=carta["seme"], forza_presa=forza))
        else:
            forza = forza_non_briscola[carta["valore"]]
            mazzo_gioco.append(
                Carta(valore=carta["valore"], seme=carta["seme"], forza_presa=forza))
    return mazzo_gioco


def distribuisci_carte(num_giocatori, mazzo):
    mani = []
    # Controlla se ci sono abbastanza carte nel mazzo per distribuire a tutti i giocatori
    if len(mazzo) < num_giocatori * 3:
        print("Non ci sono più abbastanza carte nel mazzo per distribuire a tutti i giocatori.")
        mani = []
        return mani
    else:
        for i in range(num_giocatori):
            mano = []
            for j in range(3):
                carta = mazzo.pop(0)
                mano.append(carta)
            mani.append(mano)
            print(f" carte rimanenti nel mazzo: {len(mazzo)}")

    return mani


def mostra_carte(mano):
    print(f"Giocatore {i + 1} : \n|", end="")
    for carta in mano:
        print(f"{carta.valore} di {carta.seme}", end="|")
    print("\n", end="")


def calcola_punti(mano):
    punti = 0
    for carta in mano:
        punti += carta.forza_presa
    return punti


def bussata(punti, mano, briscola):
    bussa = False
    for carta in mano:
        if carta.valore == "Asso" and carta.seme == briscola["seme"]:
            bussa = True
        elif carta.valore == "3" and carta.seme == briscola["seme"]:
            if briscola["valore"] == "Asso":
                bussa = True
            else:
                for carta2 in mano:
                    if carta2.valore == "Re" and carta2.seme == briscola["seme"]:
                        bussa = True
            break
    if punti > 120:
        bussa = True
    return bussa


def gioca_carta(turno, giocatore, mano, briscola):
    for carta in mano:
        if turno == 0 and (carta.valore == "Asso" and carta.seme == briscola["seme"]) and giocatore == bussatori[0]:
            carta_giocata = mano.pop(mano.index(carta))
        elif tavolo[0].seme == briscola["seme"] and carta.seme == briscola["seme"]:
            carta_giocata = mano.pop(mano.index(carta))
    # definire il resto della logica per giocare la carta
    return carta_giocata


def carta_vincente(carta1, carta2, briscola):
    if carta1.seme == briscola["seme"] and carta2.seme != briscola["seme"]:
        return carta1
    elif carta2.seme == briscola["seme"] and carta1.seme != briscola["seme"]:
        return carta2
    elif carta1.forza_presa > carta2.forza_presa:
        return carta1
    else:
        return carta2
    # memorizzare il giocatore che ha vinto la mano


if __name__ == "__main__":
    num_giocatori = 5  # Numero di giocatori
    num_bussatori = 0  # Numero di giocatori che bussano
    tavolo = []  # Tavolo per le carte giocate
    mescola_mazzo()
    briscola = metti_briscola()
    print(f"Briscola: {briscola}")
    assegna_forza_presa(mazzo_mescolato, briscola)
    mani = distribuisci_carte(num_giocatori, mazzo_gioco)
    print("********* Mani distribuite: chi bussa e chi affonda? *********")
    for i, mano in enumerate(mani):
        if bussata(calcola_punti(mano), mano, briscola):
            mostra_carte(mano)
            print(f"Giocatore {i + 1} ha bussato!")
            bussatori.append(num_bussatori)
            num_bussatori += 1
        else:
            mostra_carte(mano)
            print(f"Giocatore {i + 1} ha affondato!")
            affondatori.append(i)
    if num_bussatori == 0:
        print("Nessun giocatore ha bussato. Ridistribuzione delle carte.")
        exit()
    print("********** Fine giro di bussate: chi prende carte? **********")
    for i in affondatori:
        if len(bussatori) <= 3:
            print(f"Giocatore {i+1} prende carte!")
            mani[i] = distribuisci_carte(1, mazzo_gioco)
            if mani[i] not in [[], None]:
                print(f"Nuova mano per il ", end="")
                mostra_carte(mani[i][0])
                bussatori.append(num_bussatori)
                num_bussatori += 1
        else:
            print(f"Giocatore {i+1} non prende carte!")
    print("******** Lista dei partecipanti al giro *********")
    for i in bussatori:
        print(f"Giocatore {i+1} partecipa!")
    print("********** il gioco ha inizio **********")
    # Qui inizia il gioco vero e proprio, con le regole specifiche del gioco di carte
    for turn in range(3):
        print(f"\nTurno {turn + 1}:")
        for i in bussatori:
            print(f"Giocatore {i+1} gioca la carta: ", end="")
            carta_giocata = gioca_carta(turn, i, mani[i], briscola)
            print(f"{carta_giocata.valore} di {carta_giocata.seme}")
            tavolo.append(carta_giocata)




