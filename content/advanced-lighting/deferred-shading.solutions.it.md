Nel lighting pass restituisci direttamente una delle texture, riportandola nell'intervallo visibile: le normali come `n * 0.5 + 0.5`, le posizioni ridotte di scala. La demo interattiva ha un selettore per questo.
---
Con il forward rendering ogni fragment di ogni oggetto scorre tutte e 200 le luci, compresi i fragment che poi vengono nascosti. Il deferred shading esegue il ciclo una volta per pixel dello schermo. Con i volumi di luce, o con il controllo sulla distanza nello shader della demo, la maggior parte dei pixel valuta solo le poche luci che li raggiungono.
---
Passa l'inversa della matrice view-projection. Ricostruisci la posizione in clip space dalla coordinata di texture e dalla profondità salvata, trasformala e dividi per w.

{{code}}
