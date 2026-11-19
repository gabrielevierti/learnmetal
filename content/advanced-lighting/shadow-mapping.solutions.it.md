Collega la shadow map a un pass di post-processing e manda in uscita il suo valore. Dichiarala come una normale texture di profondità e leggila con un sampler ordinario, non con uno di confronto.

{{code}}

Dovresti vedere la scena dalla posizione della luce in toni di grigio. Se è tutta bianca o tutta nera, il near plane e il far plane della luce non racchiudono la scena.
---
A zero le superfici illuminate si coprono di strisce o puntini scuri: è l'acne, dovuta ai fragment che cadono appena dietro la profondità salvata nel loro texel. Con un bias grande le strisce spariscono, ma le ombre si staccano dalla base degli oggetti e gli oggetti sottili smettono di proiettare ombra: è il peter panning. La demo interattiva ha uno slider per il bias.
---
Calcola la posizione della luce dal tempo e ricostruisci la sua matrice view a ogni frame; il pass delle ombre e il pass principale devono usare la stessa matrice. Tieni la scatola ortografica centrata sulla scena, non sulla luce.
