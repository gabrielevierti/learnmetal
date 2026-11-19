{{code}}

Crea la texture di uscita con gli usi `.shaderWrite` e `.shaderRead`, poi mostrala con il triangolo a tutto schermo.
---
{{code}}

Ingresso e uscita devono essere texture diverse.
---
Aggiungi un `float3 attractor` agli uniform della simulazione e accelera ogni particella verso di esso. Per ottenere il punto, proietta la posizione del mouse su un piano davanti alla camera.

{{code}}

Il `max` tiene finita la forza quando una particella attraversa l'attrattore.
