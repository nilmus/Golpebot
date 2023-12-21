# GOLPE! sas
t.me/golpegamebot

> GOLPE! è un gioco testuale che vede diversi team contendersi il governo con la diplomazia, con l'intelligence, e con le armi.

# Per gli sviluppatori
Per runnare golpebot basta fare 4 cose:
1. scaricarlo sul vostro computer (da github o con git dal terminale)
2. installare le dependencies, copiaincollando questo nel terminale:
```
pip install -r requirements.txt
```
3. creare un file ".env" dove mettete il vostro token di telegram e i vostri dati di un database PostGreSQL, tipo così:
```
# .env

TOKEN = 'abc123'
HOST = 'abc123'
PASSWORD = 'abc123'
# etc. etc.
```
4. eseguire golpebot_2023_main.py

Fatto!

Per bug o per proporre funzioni aprite una issue qui su github,  
per integrare nel progetto il vostro codice mandate una pull request qui su github.



---
---

# Per gli utenti:

## Introduzione
Ci sono tre team: ROSSO, BLU, e NERO.
Un team è al governo, mentre gli altri due cercano di rovesciarlo tramite un GOLPE.

Le azioni disponibili sono:
- **l'attacco**: puoi sparare gli altri utenti con varie armi di diversa potenza
- **lo spionaggio**: puoi scoprire informazioni nascoste sugli altri utenti
- **la guarigione**: puoi curare i tuoi compagni feriti
- **il lavoro**: puoi guadagnare soldi
- **il commercio**: puoi comprare, scambiare e vendere armi e oggetti

Oltre a queste azioni eseguibili tramite il bot, per preparare un GOLPE serve anche una grande opera di **diplomazia**, effettuabile coi normali messaggi su telegram, sul gruppo e in privato.



## I team
Ogni team ha una gerarchia che dipende dalla forma di governo scelta.

**Per le democrazie:**
- Leader
- Parlamentari
- Soldati, spie, medici
- Cittadini

**Per le dittature:**
- Leader
- Quadri
- Soldati, spie, medici
- Sudditi

Il leader e i politici (parlamentari o quadri che siano) hanno accesso all'*ufficio* del team, da cui possono gestire faccende come le tasse, le elezioni (in democrazia), e... proclamare un GOLPE.

Ogni team ha una *cassa* di denaro.

*Entrate*:
- le **tasse**
- eventuali **donazioni** volontarie

*Uscite*:
- gli **stipendi** dei dipendenti pubblici (cioè il leader, i politici, e i soldati/spie/medici)
- **acquisti** di armi o oggetti


## Tasse
Il team al governo decide un'*aliquota* (dallo 0% al 100%).
Ogni volta che un membro di un team non al governo lavora, una parte del suo salario viene trattenuta e va direttamente nelle casse del team regnante.

Il team al governo è libero di scegliere l'aliquota che preferisce, ma secondo il principio della curva di Laffer, se esagerano con la tassazione, gli altri giocatori semplicemente smetteranno di lavorare.

*Per cambiare l'aliquota, manda /ufficio*


## Stipendi
Tutti i giocatori possono trovare un lavoro che gli consentirà di guadagnare denaro. (Più informazioni nella sezione Lavoro)

Il leader, i politici, e i soldati/spie/medici ricevono uno stipendio extra, deciso dal leader (con l'autorizzazione del parlamento, in democrazia). Questi stipendi vengono dalle casse del team, quindi se sono troppo alti, il team andrà in bancarotta.


## Lavoro
Esistono diversi lavori con parametri diversi:
- *intelligenza richiesta*: una intelligenza maggiore consente di trovare lavori più redditizi
- *salario*: i soldi. Ricorda che dal salario lordo verranno sottratte le tasse!
- *frequenza di riscossione*: alcuni lavori richiedono riscossioni più frequenti, ma ricompensano per questo con un salario giornaliero più elevato
- *durata del contratto*: alcuni lavori offrono più flessibilità, mentre altri ricompensano un impegno di lunga durata con un salario più elevato. Non è possibile rescindere un contratto

*Per trovare un lavoro, manda /trovalavoro*
*Per riscuotere il tuo stipendio, manda /lavora*


## I punti abilità
Quando ti sei registrato, hai assegnato dei punti abilità. Questi punti conferiscono dei bonus per le diverse attività. Ecco un riassunto schematico:
- **Forza**: +++++attacco
- **Intelligenza**: +++salario, ++guarigione, +spionaggio
- **Fortuna**: +++bonus oggetto, +spionaggio, +attacco
Puoi migliorare le tue abilità comprando e usando certi *oggetti*.

*Per usare gli oggetti potenziamento, manda /menu*


## Gli oggetti
Gli oggetti conferiscono un **bonus** quando li usi. Esistono bonus di diverso tipo, ma alcuni esempi sono:
- **Bonus abilità**: potenzia una o più abilità
- **Bonus salute**: restituisce punti salute
- **Bonus spionaggio**: resetta il tempo di attesa fra uno spionaggio e l'altro

I bonus abilità sono *permanenti*. Gli altri tipi di bonus sono *una tantum*.

Puoi ottenere gli oggetti in diversi modi:
- comprali dal *mercante*: di solito, questo garantisce un prezzo vicino al valore reale dell'oggetto
- comprali *da un altro utente*: se non trovi un oggetto dal mercante, potresti doverti accordare con un altro utente che ce l'ha. Quanto sei disposto a spendere?
- *fatteli regalare* da un compagno di team più forte: all'inizio, puoi chiedere un favore a chi gioca da più tempo

*Per usare gli oggetti, manda /menu*
*Per comprarli dal mercante, manda /mercante*
*Per venderli a un altro utente, manda /vendi*
*Per regalarli a un altro utente, manda /vendi e imposta il prezzo a 0*


## Le armi
Le armi servono... beh, già.

Come gli oggetti, puoi comprarle dal mercante o da un altro utente (o fartele regalare).

I parametri delle armi sono:
- **danno**: quanti punti salute toglierai alla vittima
- **rumore**: la probabilità che la vittima sappia che sei stato tu a sparare
- **forza richiesta**: le armi più potenti richiedono una forza maggiore
- **prezzo**: le armi migliori costano di più
Ogni attacco consuma una *munizione*. Puoi comprare/vendere le munizioni esattamente come le armi.

*Per usare le armi, manda /attacco*
*Per comprare dal mercante, manda /mercante*
*Per vendere a un altro utente, manda /vendi*
*Per regalare a un altro utente, manda /vendi e imposta il prezzo a 0*


## GOLPE
Prima di iniziare un GOLPE, assicurati di essere ben preparato. Compra abbastanza armi e munizioni, raccogli informazioni sui nemici attraverso lo spionaggio, addestra soldati e medici efficienti, coordinati con l'altro team non-regnante attraverso la diplomazia.

Quando pensi di essere pronto, se sei il leader del tuo team puoi dare il via al GOLPE, dall'*ufficio* del team.
Da quel momento avrete **1 ora** per portarlo a compimento.

Il GOLPE ha successo quando si verifica una di queste due condizioni:
1. **Il leader** del team regnante è caduto
2. **Il 50%+1** dei politici del team regnante è caduto

Se il GOLPE ha successo, il tuo team prenderà il governo e confischerà i beni del team sconfitto.
Se invece passa un'ora e non siete riusciti, sarà il team regnante a confiscare tutti i vostri averi.

*Per dare via al golpe, manda /ufficio*
