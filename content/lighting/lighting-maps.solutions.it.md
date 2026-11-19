Sottrai da uno il valore letto.

{{code}}
---
Nello shader non cambia niente: il termine specular è già moltiplicato per l'rgb della mappa. Una mappa dipinta di blu sopra l'acciaio dà lì riflessi blu. È così che nel modello di Phong si fanno i metalli colorati.
---
Collega una terza texture e somma il suo colore dopo l'illuminazione, senza moltiplicarlo per alcun termine della luce.

{{code}}

Per evitare che il telaio d'acciaio brilli, moltiplica l'emissione per `1.0 - step(0.01, specularColor.r)`, così compare solo dove la specular map è nera.
