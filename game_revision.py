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
    fiches: int = 100  # Fiches iniziali
    mano: List[Carta] = field(default_factory=list)
    ha_bussato: bool = False
    punti_totali: int = 0
    turni_vinti: int = 0
    carte_vinte: List[Carta] = field(default_factory=list)
    carte_scartate: List[Carta] = field(default_factory=list)

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
        self.carte_scartate.extend(self.mano)
        self.mano.clear()

    def paga(self, importo: int) -> int:
        """Paga un importo e ritorna quanto effettivamente pagato"""
        if self.fiches >= importo:
            self.fiches -= importo
            return importo
        else:
            # Paga tutto quello che ha
            pagato = self.fiches
            self.fiches = 0
            return pagato
    
    def ricevi(self, importo: int):
        """Riceve un importo in fiches"""
        self.fiches += importo

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
    PUNTATA_MAZZIERE = 3  # Fiches che il mazziere mette nel piatto


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
    """Gestisce la logica delle bussate con valutazione del rischio"""

    @staticmethod
    def ha_mano_sicura(giocatore: Giocatore, briscola: Carta) -> bool:
        """
        Verifica se il giocatore ha una mano SICURA per vincere:
        - Asso di briscola (sempre vincente)
        - 3 e Re di briscola (combinazione vincente se briscola non è Asso)
        - 3 di briscola (se briscola è Asso, 3 è la seconda carta più forte)
        """
        ha_asso_briscola = any(
            c.valore == "Asso" and c.seme == briscola.seme 
            for c in giocatore.mano
        )
        
        if ha_asso_briscola:
            return True
        
        # Controlla 3 + Re di briscola
        if briscola.valore != "Asso":
            ha_tre_briscola = any(
                c.valore == "3" and c.seme == briscola.seme 
                for c in giocatore.mano
            )
            ha_re_briscola = any(
                c.valore == "Re" and c.seme == briscola.seme 
                for c in giocatore.mano
            )
            
            if ha_tre_briscola and ha_re_briscola:
                return True
        else:
            # Briscola è Asso, controlla solo 3 di briscola
            ha_tre_briscola = any(
                c.valore == "3" and c.seme == briscola.seme 
                for c in giocatore.mano
            )
            if ha_tre_briscola:
                return True
        
        return False

    @staticmethod
    def verifica_bussata(giocatore: Giocatore, briscola: Carta, piatto: int) -> bool:
        """
        Verifica se un giocatore può/deve bussare considerando il rischio
        
        Logica:
        - Mano sicura (Asso, 3 di mano o 3+Re briscola): bussa sempre
        - Punti > soglia: bussa solo se ha abbastanza fiches
        - Altrimenti: non bussa
        """
        punti_mano = giocatore.calcola_punti_mano()
        mano_sicura = GestoreBussata.ha_mano_sicura(giocatore, briscola)
        
        # Mano sicura: bussa sempre (rischio minimo)
        if mano_sicura:
            return True
        
        # Bussata per punti alti: solo se ha abbastanza fiches per coprire il rischio
        if punti_mano > ConfigurazioneGioco.SOGLIA_PUNTI_BUSSATA:
            if giocatore.fiches >= piatto:
                return True
            else:
                return False  # Non bussa se non può permettersi di perdere
        
        return False

    @staticmethod
    def verifica_pesca_carte(giocatore: Giocatore, briscola: Carta, piatto: int) -> bool:
        """
        Verifica se un giocatore affondato dovrebbe pescare carte
        
        Logica: pesca solo se ha abbastanza fiches per coprire il rischio
        """
        return giocatore.fiches >= piatto

        return False
        
class TracciamentoCarte:
    """Traccia le carte giocate e analizza quali sono ancora in gioco"""

    def __init__(self, briscola: Carta):
        self.briscola = briscola
        self.carte_giocate: Set[Carta] = set()
        self.carte_turno_corrente: List[Carta] = []

    def registra_carta_giocata(self, carta: Carta):
        """Registra una carta giocata"""
        self.carte_giocate.add(carta)
        self.carte_turno_corrente.append(carta)

    def reset_turno(self):
        """Reset per nuovo turno"""
        self.carte_turno_corrente = []

    def carte_conosciute(self, giocatore: Giocatore) -> Set[Carta]:
        """Restituisce tutte le carte conosciute dal giocatore"""
        conosciute = set()
        conosciute.update(giocatore.mano)
        conosciute.update(giocatore.carte_scartate)
        conosciute.update(self.carte_giocate)
        return conosciute

    def briscole_piu_forti_non_uscite(self, carta: Carta, giocatore: Giocatore) -> List[Carta]:
        """
        Trova tutte le briscole più forti di 'carta' che non sono ancora uscite
        """
        if carta.seme != self.briscola.seme:
            return []

        conosciute = self.carte_conosciute(giocatore)
        briscole_piu_forti = []

        for valore in ConfigurazioneGioco.VALORI:
            carta_test = Carta(
                valore=valore,
                seme=self.briscola.seme,
                forza_presa=ConfigurazioneGioco.FORZA_BRISCOLA[valore]
            )

            # Se è più forte e non è conosciuta, potrebbe essere in giro
            if carta_test.forza_presa > carta.forza_presa and carta_test not in conosciute:
                briscole_piu_forti.append(carta_test)

        return briscole_piu_forti

    def carte_piu_forti_non_uscite(self, carta: Carta, giocatore: Giocatore) -> List[Carta]:
        """
        Trova tutte le carte dello stesso seme più forti che non sono ancora uscite
        """
        conosciute = self.carte_conosciute(giocatore)
        carte_piu_forti = []

        # Determina se la carta è briscola o no
        is_briscola = carta.seme == self.briscola.seme
        forza_dict = ConfigurazioneGioco.FORZA_BRISCOLA if is_briscola else ConfigurazioneGioco.FORZA_NON_BRISCOLA

        for valore in ConfigurazioneGioco.VALORI:
            carta_test = Carta(
                valore=valore,
                seme=carta.seme,
                forza_presa=forza_dict[valore]
            )

            if carta_test.forza_presa > carta.forza_presa and carta_test not in conosciute:
                carte_piu_forti.append(carta_test)

        return carte_piu_forti

    def esiste_briscola_piu_forte_non_uscita(self, carta: Carta, giocatore: Giocatore) -> bool:
        """Verifica se esiste almeno una briscola più forte non ancora uscita"""
        return len(self.briscole_piu_forti_non_uscite(carta, giocatore)) > 0

class GestoreTurno:
    """Gestisce la logica dei turni di gioco secondo le regole ufficiali della Bestia"""
    
    def __init__(self, briscola: Carta, tracciamento: TracciamentoCarte):
        self.briscola = briscola
        self.tracciamento = tracciamento
        self.tavolo: List[Tuple[Giocatore, Carta]] = []
        self.seme_richiesto: Optional[str] = None
        self.carta_vincente_corrente: Optional[Tuple[Giocatore, Carta]] = None
    
    def gioca_carta_strategica(self, giocatore: Giocatore, primo_turno: bool, 
                               giocatore_di_mano: bool, ultimo_a_giocare: bool) -> Carta:
        """
        Sceglie intelligentemente quale carta giocare secondo le regole della Bestia
        con strategia avanzata basata sulle carte uscite
        
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
        return self._gioca_carta_di_mano_intelligente(giocatore)

    def _gioca_carta_di_mano_intelligente(self, giocatore: Giocatore) -> Carta:
        """
        Strategia per giocatore di mano:
        - Evita di aprire con briscola se può essere battuta
        - Preferisce aprire con la non-briscola più forte
        """
        briscole = [(i, c) for i, c in enumerate(
            giocatore.mano) if c.seme == self.briscola.seme]
        non_briscole = [(i, c) for i, c in enumerate(
            giocatore.mano) if c.seme != self.briscola.seme]

        # Se ha solo briscole, gioca la più forte
        if not non_briscole:
            briscole.sort(key=lambda x: x[1].forza_presa, reverse=True)
            indice, _ = briscole[0]
            return giocatore.gioca_carta(indice)

        # Strategia: preferisci non-briscola più forte
        non_briscole.sort(key=lambda x: x[1].forza_presa, reverse=True)

        # Prendi la non-briscola più forte
        indice_migliore, carta_migliore = non_briscole[0]

        # Se ha briscole molto forti e sicure, considera di giocarle
        if briscole:
            briscole.sort(key=lambda x: x[1].forza_presa, reverse=True)
            indice_bris, carta_bris = briscole[0]

            # Se la briscola più forte è Asso o 3 e non ci sono briscole più forti in giro
            if carta_bris.valore in ["Asso", "3"]:
                if not self.tracciamento.esiste_briscola_piu_forte_non_uscita(carta_bris, giocatore):
                    # Briscola sicura! Giocala
                    return giocatore.gioca_carta(indice_bris)

        # Altrimenti gioca la non-briscola più forte
        return giocatore.gioca_carta(indice_migliore)
    
    def _gioca_carta_non_di_mano(self, giocatore: Giocatore, ultimo_a_giocare: bool) -> Carta:
        """Logica per giocatore non di mano (deve rispondere a seme)"""
        
        # Trova carte dello stesso seme richiesto
        carte_stesso_seme = [
            (i, c) for i, c in enumerate(giocatore.mano) 
            if c.seme == self.seme_richiesto
        ]
        
        if carte_stesso_seme:
            # HA carte del seme richiesto
            return self._scegli_carta_migliore(giocatore, carte_stesso_seme, ultimo_a_giocare)
        
        # NON ha carte del seme richiesto, cerca briscole
        carte_briscola = [
            (i, c) for i, c in enumerate(giocatore.mano) 
            if c.seme == self.briscola.seme
        ]
        
        if carte_briscola:
            # HA briscole, DEVE giocarle
            return self._scegli_carta_migliore(giocatore, carte_briscola, ultimo_a_giocare)
        
        # NON ha né seme richiesto né briscole, può giocare qualsiasi cosa
        # Gioca la carta più bassa
        return self._gioca_carta_piu_bassa(giocatore)
       
    def _scegli_carta_migliore(self, giocatore: Giocatore,
                               carte_valide: List[Tuple[int, Carta]],
                               ultimo_a_giocare: bool) -> Carta:
        """
        Strategia intelligente:
        - Se ultimo: cerca di vincere con la carta più bassa possibile
        - Se NON ultimo e può vincere: valuta se giocare la vincente o conservarla
        - Se NON ultimo e sono briscole: gioca la più piccola per non sprecarle
        - Se NON ultimo e sono non-briscole: gioca la più grande
        """
        
        if not self.carta_vincente_corrente:
            # Primo a giocare (non dovrebbe succedere in _scegli_carta_migliore)
            carte_valide.sort(key=lambda x: x[1].forza_presa, reverse=True)
            indice, _ = carte_valide[0]
            return giocatore.gioca_carta(indice)

        _, carta_da_battere = self.carta_vincente_corrente

        # Trova carte che possono vincere
        carte_vincenti = [
            (i, c) for i, c in carte_valide
            if self._carta_batte(c, carta_da_battere)
        ]
        
        # Se è l'ultimo a giocare
        if ultimo_a_giocare:
            if carte_vincenti:
                # Vinci con la carta più bassa possibile
                carte_vincenti.sort(key=lambda x: x[1].forza_presa)
                indice, _ = carte_vincenti[0]
                return giocatore.gioca_carta(indice)
            else:
                # Non può vincere, gioca la più bassa
                carte_valide.sort(key=lambda x: x[1].forza_presa)
                indice, _ = carte_valide[0]
                return giocatore.gioca_carta(indice)

        # NON è l'ultimo a giocare - strategia conservativa
        sono_briscole = carte_valide[0][1].seme == self.briscola.seme
                                   
        if sono_briscole:
            # Risponde con briscole
            if carte_vincenti:
                # Può vincere, ma valuta se conviene
                # Se c'è una briscola più forte in giro, gioca la più piccola
                carta_vincente_piu_bassa = min(
                    carte_vincenti, key=lambda x: x[1].forza_presa)[1]

                if self.tracciamento.esiste_briscola_piu_forte_non_uscita(carta_vincente_piu_bassa, giocatore):
                    # C'è rischio, gioca la briscola più piccola disponibile
                    carte_valide.sort(key=lambda x: x[1].forza_presa)
                    indice, _ = carte_valide[0]
                    return giocatore.gioca_carta(indice)
                else:
                    # Nessuna briscola più forte in giro, vinci!
                    indice, _ = carte_vincenti[0]
                    return giocatore.gioca_carta(indice)
            else:
                # Non può vincere con briscola, gioca la più piccola
                carte_valide.sort(key=lambda x: x[1].forza_presa)
                indice, _ = carte_valide[0]
                return giocatore.gioca_carta(indice)
        else:
            # Risponde con non-briscole
            if carte_vincenti:
                # Può vincere: gioca la vincente più bassa
                carte_vincenti.sort(key=lambda x: x[1].forza_presa)
                indice, _ = carte_vincenti[0]
                return giocatore.gioca_carta(indice)
            else:
                # Non può vincere: gioca la più GRANDE per liberarsi
                carte_valide.sort(key=lambda x: x[1].forza_presa, reverse=True)
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
        self.tracciamento.registra_carta_giocata(carta)

        if len(self.tavolo) == 1:
            self.seme_richiesto = carta.seme
            self.carta_vincente_corrente = (giocatore, carta)
        else:
            assert self.carta_vincente_corrente is not None
            if self._carta_batte(carta, self.carta_vincente_corrente[1]):
                self.carta_vincente_corrente = (giocatore, carta)
    
    def determina_vincitore(self) -> Tuple[Giocatore, List[Carta]]:
        """Determina il vincitore del turno e restituisce le carte vinte"""
        if not self.tavolo:
            raise ValueError("Nessuna carta sul tavolo!")
        assert self.carta_vincente_corrente is not None

        vincitore = self.carta_vincente_corrente[0]
        carte_vinte = [carta for _, carta in self.tavolo]

        # Reset per il prossimo turno
        self.tavolo = []
        self.seme_richiesto = None
        self.carta_vincente_corrente = None
        self.tracciamento.reset_turno()
        
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
    """Classe principale che gestisce il gioco della Bestia con sistema di scommesse"""

    def __init__(self, num_giocatori: int = 5):
        self.num_giocatori = num_giocatori
        self.mazzo = Mazzo()
        self.giocatori: List[Giocatore] = []
        self.giocatori_attivi: List[Giocatore] = []
        self.briscola: Optional[Carta] = None
        self.gestore_turno: Optional[GestoreTurno] = None
        self.tracciamento: Optional[TracciamentoCarte] = None
        self.indice_giocatore_di_mano: int = 0
        self.indice_mazziere: int = -1  # Ultimo giocatore
        self.piatto: int = 0

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
        # Inizializza tracciamento
        self.tracciamento = TracciamentoCarte(self.briscola)

        print(f"\n🃏 Briscola estratta: {self.briscola}")
        print(f"📦 Carte nel mazzo: {self.mazzo.carte_rimanenti()}\n")

        # Crea giocatori e distribuisci carte iniziali
        for i in range(self.num_giocatori):
            giocatore = Giocatore(id=i)
            carte = self.mazzo.pesca_carte(ConfigurazioneGioco.CARTE_PER_MANO)
            giocatore.aggiungi_carte(carte)
            self.giocatori.append(giocatore)

        # Il mazziere è l'ultimo giocatore
        self.indice_mazziere = self.num_giocatori - 1

    def fase_puntata_mazziere(self):
        """Il mazziere mette la puntata iniziale nel piatto"""
        mazziere = self.giocatori[self.indice_mazziere]
        puntata = mazziere.paga(ConfigurazioneGioco.PUNTATA_MAZZIERE)
        self.piatto = puntata

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
                if GestoreBussata.ha_mano_sicura(giocatore, self.briscola):
                    print(f"     🛡️  Mano SICURA!")
                giocatore.ha_bussato = True
                bussatori.append(giocatore)
            else:
                motivo = ""
                if giocatore.calcola_punti_mano() < ConfigurazioneGioco.SOGLIA_PUNTI_BUSSATA:
                    motivo = f" (punti insufficienti: {giocatore.calcola_punti_mano()} ≤ {ConfigurazioneGioco.SOGLIA_PUNTI_BUSSATA})"
                elif giocatore.fiches < self.piatto:
                    motivo = f" (fiches insufficienti: {giocatore.fiches} < {self.piatto})"
                print(f"  ❌ {giocatore} ha AFFONDATO!{motivo}")
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
               # Valuta se pescare in base alle fiches
                if GestoreBussata.verifica_pesca_carte(giocatore, self.briscola, self.piatto):
                    carte_pescate = self.mazzo.pesca_carte(
                        ConfigurazioneGioco.CARTE_PER_MANO)
                    giocatore.aggiungi_carte(carte_pescate)
                    giocatore.ha_bussato = True
                    bussatori.append(giocatore)
                    print(f"\n{giocatore} pesca {len(carte_pescate)} carte:")
                    self._mostra_mano(giocatore)
                else:
                    print(
                        f"\n{giocatore} NON pesca carte (fiches insufficienti: {giocatore.fiches} < {self.piatto})")
            else:
                print(
                    f"\n{giocatore} non può pescare carte (limite raggiunto o mazzo vuoto)")

        self.giocatori_attivi = bussatori
        print(f"\n📋 Giocatori attivi: {len(self.giocatori_attivi)}")
        print(f"💰 Piatto in palio: {self.piatto} fiches")
        print(f"   Premio per turno vinto: {self.piatto // 3} fiches")

        return True

    def gioca_partita(self):
        """Gioca l'intera partita"""
        print("\n" + "=" * 60)
        print("🎮 INIZIO PARTITA")
        print("=" * 60)
        # conferma al type checker che briscola non è None e può essere usata da GestoreTurno
        assert self.briscola is not None, "Briscola deve essere inizializzata"
        assert self.tracciamento is not None, "Tracciamento deve essere inizializzato"

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
                          offset) % num_giocatori
                giocatore = self.giocatori_attivi[indice]

                giocatore_di_mano = (offset == 0)
                primo_turno = (turno == 0)
                ultimo_a_giocare = (offset == num_giocatori - 1)

                carta_giocata = self.gestore_turno.gioca_carta_strategica(
                    giocatore, primo_turno, giocatore_di_mano, ultimo_a_giocare
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
            vincitore.turni_vinti += 1
            # Vince 1/3 del piatto
            vincitore.ricevi(premio_per_turno)

            print(f"\n  🏆 {vincitore} vince il turno! (+{punti_turno} punti)")
            # Aggiorna giocatore di mano per il prossimo turno
            self.indice_giocatore_di_mano = self.giocatori_attivi.index(vincitore)
         # Penalità per chi non ha vinto nessun turno
        print("\n" + "=" * 60)
        print("💸 FASE PENALITÀ")
        print("=" * 60)

        for giocatore in self.giocatori_attivi:
            if giocatore.turni_vinti == 0:
                penalita = giocatore.paga(self.piatto)
                print(f"\n❌ {giocatore} non ha vinto nessun turno!")
                print(
                    f"   Paga penalità: {penalita} fiches (richiesto: {self.piatto})")
                if penalita < self.piatto:
                    print(
                        f"   ⚠️  Non aveva abbastanza fiches! (rimanenti: {giocatore.fiches})")

       

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






















