Tieni un valore `exposure` nel renderer, moltiplicalo o dividilo per una costante come 1.1 finché un tasto resta premuto, e invialo negli uniform del pass di tone mapping. Moltiplicare, e non sommare, fa percepire uguale ogni passo, perché la percezione della luminosità è logaritmica.
---
Scegli in base alla coordinata di texture orizzontale.

{{code}}
