# Materiali

Acciaio, legno e plastica reagiscono in modo diverso alla stessa luce. Per descriverlo smettiamo di usare un unico colore dell'oggetto e diamo a ogni superficie un **materiale**: colori separati per i tre termini di Phong, più una shininess.

## Le struct del materiale e della luce

Le struct di MSL si possono annidare, e questo tiene leggibili gli uniform:

{{code}}

- `ambient` è il colore che la superficie mostra sotto la luce ambient, di solito uguale al suo colore diffuse.
- `diffuse` è il colore principale della superficie.
- `specular` è il colore del suo riflesso.
- `shininess` controlla quanto è stretto il riflesso.

Anche la luce ha le proprie intensità per ogni termine. La luce ambient deve essere debole, quella diffuse è il vero colore della luce, e quella specular di solito è bianco pieno.

## Lo shader

{{code}}

## Il lato Swift

Rispecchia le struct con esattezza, con i membri nello stesso ordine:

{{code}}

{{code}}

!!! warning "Controlla il layout"
    `Material` finisce con un `Float` isolato dopo tre vettori da 16 byte, quindi la sua size è 52 byte e il suo stride è 64. Qui il membro successivo, `light`, è allineato a 16 byte e comincia all'offset 64 in entrambi i linguaggi. Con le struct annidate c'è una trappola: Swift può mettere un piccolo membro successivo, per esempio un `Float`, nella coda inutilizzata della struct precedente (all'offset 52), mentre MSL non lo fa mai. Per stare tranquillo, fai seguire a una struct annidata un membro allineato a 16 byte, oppure fai finire ogni struct annidata su un multiplo di 16 byte. Quando i valori sembrano sbagliati, stampa `MemoryLayout<FragmentUniforms>.offset(of: \.viewPosition)` e confronta gli offset a mano.

## Giocare con i colori della luce

Poiché la luce ha termini separati, cambiare la luce cambia tutta l'atmosfera:

{{code}}

## Materiali reali

Da decenni circolano tabelle di valori di Phong misurati su sostanze reali. Eccone alcuni da provare, con tutti i termini della luce impostati a bianco:

| Materiale | Ambient | Diffuse | Specular | Shininess |
| --- | --- | --- | --- | --- |
| Smeraldo | 0.02, 0.17, 0.02 | 0.08, 0.61, 0.08 | 0.63, 0.73, 0.63 | 77 |
| Oro | 0.25, 0.20, 0.07 | 0.75, 0.61, 0.23 | 0.63, 0.56, 0.37 | 51 |
| Plastica ciano | 0.0, 0.1, 0.06 | 0.0, 0.51, 0.51 | 0.50, 0.50, 0.50 | 32 |
| Gomma rossa | 0.05, 0.0, 0.0 | 0.5, 0.4, 0.4 | 0.7, 0.04, 0.04 | 10 |

I materiali di Phong sono un'approssimazione grossolana. La sezione [PBR](../pbr/theory.html) li sostituisce con un modello basato sulla fisica.

## Esercizi

- Riproduci ogni materiale della tabella.
- Perché un metallo risulta più convincente quando il suo colore specular coincide con il suo colore diffuse?
