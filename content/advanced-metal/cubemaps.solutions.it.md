Disegnato per primo, la fragment function del cielo gira per ogni pixel dello schermo, e la maggior parte di quei pixel viene poi ricoperta dalla scena. Disegnato per ultimo con `.lessEqual`, gira solo dove non è stato disegnato altro. Sulle GPU Apple la hidden surface removal riduce la differenza per i disegni opachi, ma disegnare il cielo per ultimo non è mai più lento.
---
Usa l'effetto Fresnel: più riflessione agli angoli radenti.

{{code}}

Nella demo interattiva sostituisci l'ultima riga dello shader con questa per avere una sfera di vetro dai bordi riflettenti.
