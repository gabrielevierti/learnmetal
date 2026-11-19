# Riepilogo

Ora sai illuminare una scena. Il modello è semplice, ed è la base che ogni tecnica successiva raffina.

## Glossario

- **Vettore colore**: le intensità di rosso, verde e blu. La riflessione è una moltiplicazione componente per componente tra il colore della luce e quello della superficie.
- **Modello di illuminazione di Phong**: ambient + diffuse + specular.
- **Ambient**: un termine costante che imita la luce indiretta.
- **Diffuse**: la luminosità data dall'angolo tra la normale e la direzione verso la luce: `max(dot(N, L), 0)`.
- **Specular**: un riflesso dato dall'angolo tra la luce riflessa e la direzione verso chi guarda, elevato all'esponente di shininess.
- **Normale**: un vettore unitario perpendicolare alla superficie.
- **Matrice delle normali**: la trasposta dell'inversa del blocco 3×3 in alto a sinistra della matrice model, usata per trasformare correttamente le normali.
- **Materiale**: l'insieme dei valori che descrivono come una superficie reagisce alla luce.
- **Diffuse map / specular map**: texture che forniscono pixel per pixel il colore e la lucentezza del materiale.
- **Luce direzionale**: raggi paralleli, con una direzione e nessuna posizione.
- **Luce puntiforme**: una posizione, luce in tutte le direzioni e attenuazione con la distanza.
- **Attenuazione**: il calo della luce con la distanza.
- **Spot**: una luce puntiforme limitata a un cono, con un bordo morbido tra un cutoff interno e uno esterno.

## Che cosa è cambiato nel renderer

- `VertexOut` porta alla fragment function la posizione e la normale in spazio mondo.
- Gli uniform del vertice hanno guadagnato una matrice delle normali.
- Una seconda struct di uniform, collegata allo slot 1 dei buffer del fragment, contiene le luci, la posizione della camera e i valori del materiale.
- Le luci presenti in numero variabile vivono in un loro buffer e si indicizzano attraverso un puntatore.
- Due pipeline state condividono una sola vertex function: uno illuminato per gli oggetti e uno senza illuminazione per le lampade.

## Dove il modello non basta

L'illuminazione di Phong è un'approssimazione artistica. I suoi punti deboli indicano direttamente i capitoli che verranno:

- I riflessi si rompono agli angoli radenti. Vedi [Blinn-Phong](../advanced-lighting/blinn-phong.html).
- I colori sono calcolati nello spazio colore sbagliato. Vedi [Correzione gamma](../advanced-lighting/gamma-correction.html).
- Niente proietta ombra. Vedi [Shadow mapping](../advanced-lighting/shadow-mapping.html).
- Le superfici piatte sembrano piatte. Vedi [Normal mapping](../advanced-lighting/normal-mapping.html).
- I materiali non conservano l'energia e vanno regolati a mano scena per scena. Vedi [PBR](../pbr/theory.html).

Prima di tutto questo, però, i cubi stanno diventando noiosi. La prossima sezione carica modelli veri.
