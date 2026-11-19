Usa una direzione quasi orizzontale, per esempio (-1.0, -0.15, -0.3), e un colore diffuse come (1.0, 0.55, 0.25), con un ambient debole e bluastro come (0.05, 0.06, 0.1). Le lunghe sfumature e i riflessi caldi fanno il resto.
---
Parti dalla tabella: per una portata di circa 13 unità usa 0.35 per il lineare e 0.44 per il quadratico. Alza il termine quadratico per far spegnere prima la luce senza scurire ciò che è vicino; alza quello lineare per scurire tutto in modo più uniforme.
---
Costruisci una matrice view-projection per lo spot, come per una camera messa nella luce che guarda lungo la sua direzione. Trasforma con essa la posizione in spazio mondo del fragment, dividi per w e porta da -1...1 a 0...1 per ottenere una coordinata di texture. Moltiplica il colore della luce per l'immagine letta.

{{code}}

È la prima metà dello shadow mapping: più avanti la stessa proiezione leggerà una profondità invece di un colore.
