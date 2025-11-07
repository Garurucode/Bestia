"""
Gioco della Bestia - Versione Refactorizzata con Regole Ufficiali
Struttura modulare, orientata agli oggetti, facilmente estendibile
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple
from enum import Enum


# ==================== MODELLI ====================

class Seme(Enum):
    """Enum per i semi delle carte napoletane"""
    COPPE = "coppe"
    DENARI = "denari"
    SPADE = "spade"
    BASTONI = "bastoni"


class Valore(Enum):
    """Enum per i valori delle carte"""
    ASSO = "Asso"
    DUE = "2"
    TRE = "3"
    QUATTRO = "4"
    CINQUE = "5"
    SEI = "6"
    SETTE = "7"
    FANTE = "Fante"
    CAVALLO = "Cavallo"
    RE = "Re"


@dataclass
class Carta:
    """Rappresenta una carta da gioco"""
    valore: str
    seme: str
    forza_presa: int = 0

    def __str__(self):
        return f"{self.valore} di {self.seme}"
        
    def __eq__(self, other):
        if not isinstance(other, Carta):
            return False
        return self.valore == other.valore and self.seme == other.seme

    def __hash__(self):
        return hash((self.valore, self.seme))


@dataclass
class Giocatore:
    """Rappresenta un giocatore"""
    id: int
    mano: List[Carta] = field(default_factory=list)
    ha_bussato: bool = False
    punti_totali: int = 0
    carte_vinte: List[Carta] = field(default_factory=list)

    def aggiungi_carte(self, carte: List[Carta]):
        """Aggiunge carte alla mano del giocatore"""
        self.mano.extend(carte)

    def gioca_carta(self, indice: int = 0) -> Carta:
        """Rimuove e restituisce una carta dalla mano"""
        if not self.mano:
            raise ValueError(f"Giocatore {self.id} non ha carte!")
        return self.mano.pop(indice)

    def calcola_punti_mano(self) -> int:
        """Calcola i punti totali delle carte in mano"""
        return sum(carta.forza_presa for carta in self.mano)

    def scarta_mano(self) -> None:
        """Scarta tutte le carte dalla mano"""
        self.mano.clear()

    def __str__(self):
        return f"Giocatore {self.id + 1}"


# ==================== CONFIGURAZIONE GIOCO ====================

class ConfigurazioneGioco:
    """Configurazione statica del gioco"""

    # Forza delle carte non briscola
    FORZA_NON_BRISCOLA = {
        "Asso": 90, "3": 80, "Re": 60, "Cavallo": 50, "Fante": 40,
        "7": 20, "6": 15, "5": 10, "4": 5, "2": 2
    }

    # Forza delle carte briscola
    FORZA_BRISCOLA = {
        "Asso": 100, "3": 95, "Re": 85, "Cavallo": 75, "Fante": 65,
        "7": 55, "6": 50, "5": 45, "4": 40, "2": 35
    }

    SEMI = ["coppe", "denari", "spade", "bastoni"]
    VALORI = ["Asso", "2", "3", "4", "5", "6", "7", "Fante", "Cavallo", "Re"]
    CARTE_PER_MANO = 3
    SOGLIA_PUNTI_BUSSATA = 150


# ==================== LOGICA GIOCO ====================

class Mazzo:
    """Gestisce il mazzo di carte"""

    def __init__(self):
        self.carte: List[Carta] = []
        self.briscola: Optional[Carta] = None

    def crea_mazzo(self) -> None:
        """Crea un mazzo completo di carte napoletane"""
        self.carte = [
            Carta(valore=valore, seme=seme)
            for valore in ConfigurazioneGioco.VALORI
            for seme in ConfigurazioneGioco.SEMI
        ]

    def mescola(self) -> None:
        """Mescola il mazzo"""
        random.shuffle(self.carte)

    def estrai_briscola(self) -> Carta:
        """Estrae la prima carta come briscola"""
        if not self.carte:
            raise ValueError("Mazzo vuoto!")
        self.briscola = self.carte.pop(0)
        return self.briscola

    def assegna_forza_carte(self) -> None:
        """Assegna la forza di presa a tutte le carte in base alla briscola"""
        if not self.briscola:
            raise ValueError("Briscola non definita!")

        for carta in self.carte:
            if carta.seme == self.briscola.seme:
                carta.forza_presa = ConfigurazioneGioco.FORZA_BRISCOLA[carta.valore]
            else:
                carta.forza_presa = ConfigurazioneGioco.FORZA_NON_BRISCOLA[carta.valore]

    def pesca_carte(self, num_carte: int) -> List[Carta]:
        """Pesca un numero di carte dal mazzo"""
        if len(self.carte) < num_carte:
            return []
        return [self.carte.pop(0) for _ in range(num_carte)]

    def carte_rimanenti(self) -> int:
        """Restituisce il numero di carte rimanenti"""
        return len(self.carte)


class GestoreBussata:
    """Gestisce la logica delle bussate"""

    @staticmethod
    def verifica_bussata(giocatore: Giocatore, briscola: Carta) -> bool:
        """Verifica se un giocatore può/deve bussare"""
        punti_mano = giocatore.calcola_punti_mano()

        # Bussata automatica se supera la soglia punti
        if punti_mano > ConfigurazioneGioco.SOGLIA_PUNTI_BUSSATA:
            return True

        # Verifica se ha Asso di briscola
        for carta in giocatore.mano:
            if carta.valore == "Asso" and carta.seme == briscola.seme:
                return True

            # Verifica 3 di briscola con condizioni
            if carta.valore == "3" and carta.seme == briscola.seme:
                if briscola.valore == "Asso":
                    return True
                # Verifica se ha anche Re di briscola
                for carta2 in giocatore.mano:
                    if carta2.valore == "Re" and carta2.seme == briscola.seme:
                        return True

        return False


class GestoreTurno:
    """Gestisce la logica dei turni di gioco secondo le regole ufficiali della Bestia"""
    
    def __init__(self, briscola: Carta):
        self.briscola = briscola
        self.tavolo: List[tuple[Giocatore, Carta]] = []
        self.seme_richiesto: Optional[str] = None
        self.carta_vincente_corrente: Optional[tuple[Giocatore, Carta]] = None
    
    def gioca_carta_strategica(self, giocatore: Giocatore, primo_turno: bool, 
                               giocatore_di_mano: bool) -> Carta:
        """
        Sceglie intelligentemente quale carta giocare secondo le regole della Bestia
        
        Regole:
        1. Giocatore di mano al primo turno con Asso di briscola: DEVE giocarlo
        2. Non di mano: DEVE rispondere a seme se possibile
        3. Se non ha il seme: DEVE giocare briscola se ne ha
        4. Altrimenti: può giocare qualsiasi carta
        
        Strategia:
        - Cerca di vincere giocando la carta più bassa che vince
        - Se non può vincere, gioca la carta più bassa (preferendo non briscole)
        """
        
        if not giocatore.mano:
            raise ValueError(f"{giocatore} non ha carte da giocare!")
        
        # REGOLA 1: Giocatore di mano al primo turno con Asso di briscola
        if giocatore_di_mano and primo_turno:
            for i, carta in enumerate(giocatore.mano):
                if carta.valore == "Asso" and carta.seme == self.briscola.seme:
                    return giocatore.gioca_carta(i)
        
        # REGOLA 2-3-4: Giocatore non di mano
        if not giocatore_di_mano and self.seme_richiesto:
            return self._gioca_carta_non_di_mano(giocatore)
        
        # Giocatore di mano (non primo turno) o primo turno senza Asso di briscola
        return self._gioca_carta_di_mano(giocatore)
    
    def _gioca_carta_non_di_mano(self, giocatore: Giocatore) -> Carta:
        """Logica per giocatore non di mano (deve rispondere a seme)"""
        
        # Trova carte dello stesso seme richiesto
        carte_stesso_seme = [
            (i, c) for i, c in enumerate(giocatore.mano) 
            if c.seme == self.seme_richiesto
        ]
        
        if carte_stesso_seme:
            # HA carte del seme richiesto
            return self._scegli_carta_migliore(giocatore, carte_stesso_seme)
        
        # NON ha carte del seme richiesto, cerca briscole
        carte_briscola = [
            (i, c) for i, c in enumerate(giocatore.mano) 
            if c.seme == self.briscola.seme
        ]
        
        if carte_briscola:
            # HA briscole, DEVE giocarle
            return self._scegli_carta_migliore(giocatore, carte_briscola)
        
        # NON ha né seme richiesto né briscole, può giocare qualsiasi cosa
        # Gioca la carta più bassa
        return self._gioca_carta_piu_bassa(giocatore)
    
    def _gioca_carta_di_mano(self, giocatore: Giocatore) -> Carta:
        """Logica per giocatore di mano (sceglie liberamente)"""
        
        # Strategia semplice: gioca la carta più forte (non tiene conto delle carte giocate)
        # Per ora gioca la prima carta disponibile
        carte_disponibili = [(i, c) for i, c in enumerate(giocatore.mano)]
        
        # Preferisci giocare carte alte per prendere
        carte_disponibili.sort(key=lambda x: x[1].forza_presa, reverse=True)
        indice, _ = carte_disponibili[0]
        return giocatore.gioca_carta(indice)
    
    def _scegli_carta_migliore(self, giocatore: Giocatore, 
                               carte_valide: List[tuple[int, Carta]]) -> Carta:
        """
        Sceglie la carta migliore tra quelle valide:
        - Se può vincere: gioca la carta più bassa che vince
        - Se non può vincere: gioca la carta più bassa in assoluto
        """
        
        if not self.carta_vincente_corrente:
            # È il primo a giocare, gioca carta più alta
            carte_valide.sort(key=lambda x: x[1].forza_presa, reverse=True)
            indice, _ = carte_valide[0]
            return giocatore.gioca_carta(indice)
        
        _, carta_da_battere = self.carta_vincente_corrente
        
        # Trova carte che possono vincere
        carte_vincenti = [
            (i, c) for i, c in carte_valide 
            if self._carta_batte(c, carta_da_battere)
        ]
        
        if carte_vincenti:
            # Può vincere: gioca la carta vincente più bassa
            carte_vincenti.sort(key=lambda x: x[1].forza_presa)
            indice, _ = carte_vincenti[0]
            return giocatore.gioca_carta(indice)
        
        # Non può vincere: gioca la carta più bassa
        carte_valide.sort(key=lambda x: x[1].forza_presa)
        indice, _ = carte_valide[0]
        return giocatore.gioca_carta(indice)
    
    def _gioca_carta_piu_bassa(self, giocatore: Giocatore) -> Carta:
        """Gioca la carta più bassa, preferendo non briscole"""
        
        # Separa briscole e non briscole
        non_briscole = [(i, c) for i, c in enumerate(giocatore.mano) 
                        if c.seme != self.briscola.seme]
        briscole = [(i, c) for i, c in enumerate(giocatore.mano) 
                    if c.seme == self.briscola.seme]
        
        # Preferisci non briscole
        if non_briscole:
            non_briscole.sort(key=lambda x: x[1].forza_presa)
            indice, _ = non_briscole[0]
        else:
            briscole.sort(key=lambda x: x[1].forza_presa)
            indice, _ = briscole[0]
        
        return giocatore.gioca_carta(indice)
    
    def aggiungi_carta_tavolo(self, giocatore: Giocatore, carta: Carta):
        """Aggiunge una carta giocata al tavolo"""
        self.tavolo.append((giocatore, carta))
        
        # Se è la prima carta, imposta il seme richiesto
        if len(self.tavolo) == 1:
            self.seme_richiesto = carta.seme
            self.carta_vincente_corrente = (giocatore, carta)
        else:
            # Aggiorna la carta vincente se necessario
            assert self.carta_vincente_corrente is not None, "Carta vincente corrente non definita!"
            if self._carta_batte(carta, self.carta_vincente_corrente[1]):
                self.carta_vincente_corrente = (giocatore, carta)
    
    def determina_vincitore(self) -> tuple[Giocatore, List[Carta]]:
        """Determina il vincitore del turno e restituisce le carte vinte"""
        if not self.tavolo:
            raise ValueError("Nessuna carta sul tavolo!")
        assert self.carta_vincente_corrente is not None, "Carta vincente corrente non definita!"
        vincitore = self.carta_vincente_corrente[0]
        carte_vinte = [carta for _, carta in self.tavolo]
        
        # Reset per il prossimo turno
        self.tavolo = []
        self.seme_richiesto = None
        self.carta_vincente_corrente = None
        
        return vincitore, carte_vinte
    
    def _carta_batte(self, carta1: Carta, carta2: Carta) -> bool:
        """
        Verifica se carta1 batte carta2 secondo le regole della Bestia:
        - Briscola batte sempre non-briscola
        - Tra carte dello stesso seme, vince la più forte
        - Carta di seme diverso (non briscola) NON batte mai
        """
        
        carta1_briscola = carta1.seme == self.briscola.seme
        carta2_briscola = carta2.seme == self.briscola.seme
        
        # Briscola vs non-briscola
        if carta1_briscola and not carta2_briscola:
            return True
        if carta2_briscola and not carta1_briscola:
            return False
        
        # Entrambe briscole o stesso seme: confronta forza
        if carta1.seme == carta2.seme:
            return carta1.forza_presa > carta2.forza_presa
        
        # Semi diversi (nessuna briscola): carta1 non batte
        return False


# ==================== GIOCO PRINCIPALE ====================

class BriscolaGame:
    """Classe principale che gestisce il gioco della Briscola"""

    def __init__(self, num_giocatori: int = 5):
        self.num_giocatori = num_giocatori
        self.mazzo = Mazzo()
        self.giocatori: List[Giocatore] = []
        self.giocatori_attivi: List[Giocatore] = []
        self.briscola: Optional[Carta] = None
        self.gestore_turno: Optional[GestoreTurno] = None
        self.indice_giocatore_di_mano: int = 0

    def _verifica_inizializzazione(self):
        """Verifica che il gioco sia stato inizializzato"""
        if not self.briscola:
            raise ValueError(
                "Il gioco non è stato inizializzato! "
                "Chiama inizializza_gioco() prima."
            )

    def inizializza_gioco(self):
        """Inizializza il gioco: crea mazzo, mescola, distribuisce carte"""
        print("=" * 60)
        print("🎴 INIZIALIZZAZIONE GIOCO DELLA BESTIA 🎴")
        print("=" * 60)

        # Crea e prepara il mazzo
        self.mazzo.crea_mazzo()
        self.mazzo.mescola()
        self.briscola = self.mazzo.estrai_briscola()
        self.mazzo.assegna_forza_carte()

        print(f"\n🃏 Briscola estratta: {self.briscola}")
        print(f"📦 Carte nel mazzo: {self.mazzo.carte_rimanenti()}\n")

        # Crea giocatori e distribuisci carte iniziali
        for i in range(self.num_giocatori):
            giocatore = Giocatore(id=i)
            carte = self.mazzo.pesca_carte(ConfigurazioneGioco.CARTE_PER_MANO)
            giocatore.aggiungi_carte(carte)
            self.giocatori.append(giocatore)

    def fase_bussate(self):
        """Gestisce la fase delle bussate"""
        print("=" * 60)
        print("👊 FASE BUSSATE")
        print("=" * 60 + "\n")

        bussatori = []
        affondatori = []
        # conferma al type checker che briscola non è None e può essere usata da verifica_bussata
        assert self.briscola is not None, "Briscola deve essere inizializzata"

        for giocatore in self.giocatori:
            print(f"\n{giocatore}:")
            self._mostra_mano(giocatore)

            if GestoreBussata.verifica_bussata(giocatore, self.briscola):
                print(
                    f"  ✅ {giocatore} ha BUSSATO! (Punti: {giocatore.calcola_punti_mano()})")
                giocatore.ha_bussato = True
                bussatori.append(giocatore)
            else:
                print(f"  ❌ {giocatore} ha AFFONDATO!")
                giocatore.scarta_mano()
                affondatori.append(giocatore)

        # Gestisci caso nessuno bussa
        if not bussatori:
            print("\n⚠️  Nessun giocatore ha bussato. Fine partita.")
            return False

        # Gestisci pescata carte per affondatori
        print("\n" + "=" * 60)
        print("🎣 FASE PESCATA CARTE")
        print("=" * 60)

        for giocatore in affondatori:
            if len(bussatori) <= 3 and self.mazzo.carte_rimanenti() >= ConfigurazioneGioco.CARTE_PER_MANO:
                carte_pescate = self.mazzo.pesca_carte(
                    ConfigurazioneGioco.CARTE_PER_MANO)
                giocatore.aggiungi_carte(carte_pescate)
                giocatore.ha_bussato = True
                bussatori.append(giocatore)
                print(f"\n{giocatore} pesca {len(carte_pescate)} carte:")
                self._mostra_mano(giocatore)
            else:
                print(
                    f"\n{giocatore} non può pescare carte (limite raggiunto o mazzo vuoto)")

        self.giocatori_attivi = bussatori
        print(f"\n📋 Giocatori attivi: {len(self.giocatori_attivi)}")

        return True

    def gioca_partita(self):
        """Gioca l'intera partita"""
        print("\n" + "=" * 60)
        print("🎮 INIZIO PARTITA")
        print("=" * 60)
        # conferma al type checker che briscola non è None e può essere usata da GestoreTurno
        assert self.briscola is not None, "Briscola deve essere inizializzata"

        self.gestore_turno = GestoreTurno(self.briscola)
        self.indice_giocatore_di_mano = 0  # Il primo giocatore è di mano

        # Gioca 3 turni (tutte le carte)
        for turno in range(ConfigurazioneGioco.CARTE_PER_MANO):
            print(f"\n{'─' * 60}")
            print(f"🎯 TURNO {turno + 1}/{ConfigurazioneGioco.CARTE_PER_MANO}")
            print('─' * 60)

            # Ogni giocatore gioca una carta nell'ordine corretto
            for offset in range(len(self.giocatori_attivi)):
                # Calcola l'indice con rotazione partendo dal giocatore di mano
                indice = (self.indice_giocatore_di_mano +
                          offset) % len(self.giocatori_attivi)
                giocatore = self.giocatori_attivi[indice]

                giocatore_di_mano = (offset == 0)
                primo_turno = (turno == 0)

                carta_giocata = self.gestore_turno.gioca_carta_strategica(
                    giocatore, primo_turno, giocatore_di_mano
                )
                self.gestore_turno.aggiungi_carta_tavolo(
                    giocatore, carta_giocata)

                marcatore = "👉 [DI MANO]" if giocatore_di_mano else ""
                print(f"  {giocatore} gioca: {carta_giocata} {marcatore}")

            # Determina vincitore del turno
            vincitore, carte_vinte = self.gestore_turno.determina_vincitore()
            vincitore.carte_vinte.extend(carte_vinte)
            punti_turno = sum(c.forza_presa for c in carte_vinte)
            vincitore.punti_totali += punti_turno

            print(f"\n  🏆 {vincitore} vince il turno! (+{punti_turno} punti)")
            self.indice_giocatore_di_mano = self.giocatori_attivi.index(vincitore)

    def mostra_risultati(self):
        """Mostra i risultati finali"""
        print("\n" + "=" * 60)
        print("📊 RISULTATI FINALI")
        print("=" * 60 + "\n")

        # Ordina giocatori per punti
        classifica = sorted(
            self.giocatori_attivi,
            key=lambda g: g.punti_totali,
            reverse=True
        )

        for i, giocatore in enumerate(classifica, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji} {i}° - {giocatore}: {giocatore.punti_totali} punti "
                  f"({len(giocatore.carte_vinte)} carte vinte)")

        print("\n" + "=" * 60)

    def _mostra_mano(self, giocatore: Giocatore):
        """Mostra le carte in mano di un giocatore"""
        print(f"  Mano: ", end="")
        for carta in giocatore.mano:
            print(f"| {carta} ", end="")
        print("|")

    def avvia(self):
        """Avvia l'intero gioco dall'inizio alla fine"""
        self.inizializza_gioco()

        if self.fase_bussate():
            self.gioca_partita()
            self.mostra_risultati()


# ==================== ESECUZIONE ====================

if __name__ == "__main__":
    # Crea e avvia una partita
    game = BriscolaGame(num_giocatori=5)
    game.avvia()

    print("\n✅ Partita completata!")
    print("\n💡 Per giocare di nuovo: game = BriscolaGame(num_giocatori=5); game.avvia()")








