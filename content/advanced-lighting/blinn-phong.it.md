# Blinn-Phong

Il termine specular di Phong ha un difetto che si nota sulle superfici ruvide viste con un angolo basso. Una piccola modifica alla formula, proposta da James Blinn nel 1977, lo corregge, e da allora è la scelta predefinita.

## Il problema di Phong

Phong misura l'angolo tra la **direzione di vista** e la **direzione della luce riflessa**. Quando chi guarda e la luce stanno dallo stesso lato di una superficie, ed entrambi vicini all'orizzonte, quell'angolo può superare i 90 gradi. Il prodotto scalare diventa negativo e viene portato a zero, così il riflesso si interrompe di colpo.

Con un esponente di shininess alto il riflesso è minuscolo e la zona del taglio non viene mai raggiunta. Con un esponente basso, come nel caso di un riflesso largo e morbido su un pavimento, ottieni un bordo netto ben visibile dove la luce speculare finisce all'improvviso.

## Il vettore halfway

Blinn-Phong sostituisce il vettore di riflessione con il **vettore halfway**: il vettore unitario esattamente a metà tra la direzione della luce e la direzione di vista.

{{code}}

L'intensità speculare dipende allora dall'angolo tra il vettore halfway e la **normale**:

{{code}}

Quando la direzione di vista si allinea perfettamente con la riflessione, il vettore halfway si allinea con la normale, quindi i due modelli sono d'accordo su dove il riflesso è più luminoso. La differenza è che l'angolo tra la normale e il vettore halfway non supera mai i 90 gradi finché la luce sta sopra la superficie, quindi il taglio non può avvenire.

## Nello shader

Cambiano solo le righe dello specular nelle funzioni di illuminazione:

{{code}}

## Regolare la shininess

L'angolo con il vettore halfway è più piccolo di quello usato da Phong, circa la metà. A parità di esponente, quindi, Blinn-Phong dà un riflesso più grande. Per avere un aspetto simile moltiplica i vecchi valori di shininess per un numero tra 2 e 4.

## Una scena di prova

Stendi un grande pavimento con texture sotto una sola luce puntiforme vicina alla superficie, e aggiungi un uniform che passa da una formula all'altra:

{{code}}

Con Phong il riflesso sul pavimento è troncato lungo una curva. Con Blinn-Phong sfuma dolcemente e si allunga verso l'orizzonte, che è come si comportano i veri pavimenti lucidi.

!!! note "I booleani negli uniform"
    Il `bool` di MSL occupa un byte, e così il `Bool` di Swift, ma è facile sbagliare l'allineamento e il padding intorno a loro. Molti nelle struct di uniform usano un flag `uint` o `int` (`UInt32` in Swift) per tenere i layout evidenti.

Blinn-Phong viene usato per il resto di questa sezione. Resta un modello empirico, e la sezione PBR lo sostituirà, ma il vettore halfway rimane: è centrale anche nella riflessione speculare fisicamente corretta.
