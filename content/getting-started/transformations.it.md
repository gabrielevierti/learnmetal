# Trasformazioni

Finora gli oggetti stanno dove li mettono i loro vertici. Per muoverli, ruotarli e scalarli senza riscrivere i vertex buffer a ogni frame, moltiplichiamo ogni vertice per una **matrice**. Questo capitolo è un giro rapido nella matematica, seguito da un piccolo file di supporto in Swift che useremo per il resto della serie.

## Vettori

Un vettore è una direzione con una lunghezza. In grafica usiamo i vettori anche per le posizioni (una direzione a partire dall'origine) e per i colori. Le operazioni che contano:

- **Somma e sottrazione** lavorano componente per componente. `b - a` è il vettore che punta da `a` a `b`.
- **Lunghezza**: `length(v)` è la radice quadrata di `x² + y² + z²`. Un vettore di lunghezza 1 è un **vettore unitario**, e `normalize(v)` porta qualsiasi vettore a lunghezza 1.
- **Prodotto scalare**: `dot(a, b) = a.x*b.x + a.y*b.y + a.z*b.z`. Per vettori unitari è uguale al coseno dell'angolo tra i due: 1 se sono paralleli, 0 se perpendicolari, -1 se opposti. Tutta l'illuminazione si costruisce su questo.
- **Prodotto vettoriale**: `cross(a, b)` è un vettore perpendicolare a entrambi.

Il modulo `simd` di Swift li fornisce tutti, con gli stessi nomi di MSL.

## Matrici

Una matrice 4×4 può esprimere qualsiasi combinazione di scala, rotazione e traslazione. Moltiplicare una matrice per un vettore applica la trasformazione.

La **scala** mette i fattori sulla diagonale. La **traslazione** mette lo spostamento nell'ultima colonna, ed è per questo che servono quattro dimensioni: una matrice 3×3 non può spostare un punto. La quarta componente di un vettore, **w**, accende e spegne la traslazione. Le posizioni usano `w = 1` e vengono spostate; le direzioni usano `w = 0` e no.

La **rotazione** di un angolo intorno a un asse riempie il blocco 3×3 in alto a sinistra di seni e coseni. È raro scriverla a mano.

## L'ordine conta

Il prodotto tra matrici non è commutativo. Con i vettori colonna, che è la convenzione sia di Metal sia di `simd`, la matrice **più vicina al vettore si applica per prima**:

{{code}}

Scala, poi ruota, poi trasla: è l'ordine che vuoi quasi sempre. Traslare prima e ruotare dopo fa girare l'oggetto intorno all'origine come un sasso legato a una corda.

## Un file di supporto per le matrici

`simd` ci dà i tipi ma pochi costruttori. Aggiungi `Math.swift`:

{{code}}

Gli angoli sono ovunque in radianti; `45.radians` converte dai gradi. Le matrici sono memorizzate in ordine **column-major**: `columns.3` è la quarta colonna, dove vive la traslazione. Il `float4x4` di MSL usa lo stesso layout, quindi una matrice Swift si può copiare tale e quale in un buffer di uniform.

La rotazione è costruita a partire da un **quaternione**, una rappresentazione della rotazione con quattro numeri che non soffre del gimbal lock, il problema delle rotazioni concatenate attorno agli assi. Per usarlo non serve conoscerne la teoria.

## Trasformare il rettangolo

Aggiungi una matrice agli uniform e moltiplica nella vertex function:

{{code}}

Gli uniform usano lo slot **1** dei buffer di vertice perché lo slot 0 contiene i dati dei vertici. Da qui in avanti è la nostra convenzione: slot 0 per i vertici, slot 1 per gli uniform.

{{code}}

Ora il rettangolo è grande la metà, sta nell'angolo in basso a destra e gira intorno al proprio centro. Se la finestra non è quadrata, mentre ruota appare deformato. È previsto, e la matrice di proiezione del prossimo capitolo lo sistema.

## Esercizi

- Scambia la traslazione con la rotazione e prova a prevedere il risultato prima di eseguire.
- Disegna il rettangolo una seconda volta nell'angolo in alto a sinistra, con una scala che segue `sin(time)`. Ti servono solo un secondo `setVertexBytes` e una seconda draw call.
