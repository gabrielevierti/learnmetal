Passa `MTLSize(width: 64, height: 64, depth: 1)` e ottieni 4.096 rettangoli. Non cambia nient'altro, perché ogni threadgroup calcola la propria posizione da `threadgroup_position_in_grid`. Regola lo scarto `- 16.0` per tenere centrato il campo.
---
Decidi in base alla posizione del gruppo e scrivi il conteggio di conseguenza. I vertici scritti per una mesh con zero primitive vengono ignorati.

{{code}}
---
Metti il livello di dettaglio nel payload, leggilo nella mesh function e trasformalo in un colore.

{{code}}

I cluster vicini sono verdi, quelli intermedi gialli e quelli lontani rossi, e puoi guardare le fasce spostarsi insieme alla camera.
