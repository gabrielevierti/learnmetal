Ogni coppia di pass allarga un po' la sfocatura, perché le sfocature gaussiane ripetute si sommano. Due iterazioni danno un bagliore stretto intorno alle lampade; venti danno una foschia ampia, a un costo venti volte maggiore. Quel costo è la ragione dell'approccio con la catena di mip.
---
Fai le due texture della sfocatura grandi la metà della scena. La sfocatura costa allora un quarto e copre a ogni pass il doppio della distanza sullo schermo. Poiché il bagliore è morbido, la risoluzione più bassa non si nota dopo l'ingrandimento finale.
---
Crea una catena di texture, ognuna grande la metà della precedente. Riduci la texture luminosa in ogni livello con un piccolo filtro, poi risali: ingrandisci il livello n, sommalo al livello n - 1 e ripeti fino in cima. La demo interattiva qui sopra usa come catena di riduzione le mipmap della texture stessa e somma cinque livelli in un solo pass.
