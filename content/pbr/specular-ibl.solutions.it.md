Nello shader dello skybox leggi la cubemap prefiltrata a un livello fisso.

{{code}}

Il livello 0 è l'ambiente nitido e ogni livello superiore è più sfocato.
---
La irradiance map, la mappa prefiltrata e la tabella di lookup dipendono solo dall'ambiente, e la tabella nemmeno da quello. Dopo averle generate, rileggi ogni livello di mip e ogni faccia con un blit in un buffer e scrivi i byte in un file; all'avvio successivo riempi le texture con `replace`. Un contenitore diffuso per questo scopo è KTX.
---
Del materiale non cambia niente. Rigenera la irradiance map e la mappa prefiltrata per ogni ambiente e collegale. Lo stesso oggetto appare tinto di blu sotto un cielo aperto e caldo in un tramonto, ed è questo il vantaggio pratico dei materiali fisicamente corretti.
