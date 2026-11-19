Da fuori non cambia niente. Appena la camera entra nel cubo vedi solo il colore di sfondo: ora ogni faccia è vista da dietro, e vengono scartate tutte. La demo interattiva mostra il caso opposto quando scegli `.front`.
---
Scambia due dei tre vertici di ogni triangolo di quella faccia. Vista da fuori, ora quella faccia è in senso orario, quindi viene trattata come posteriore e scartata, lasciando un buco attraverso cui vedi l'interno del cubo, che viene scartato anch'esso.
---
È lo shader della demo interattiva qui sopra: prendi un parametro `bool` marcato `[[front_facing]]` e scegli il colore in base a quello. Se illumini le facce posteriori, inverti la normale.
