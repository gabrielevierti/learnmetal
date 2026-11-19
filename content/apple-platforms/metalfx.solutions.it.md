Crea lo scaler con l'ingresso a metà dimensione e l'uscita alla dimensione del drawable, codificalo dopo il pass della scena e fai leggere al pass finale la texture ingrandita. Bordi e dettaglio delle texture sono visibilmente più netti che con il filtro lineare, che si limita a sfocare. Le linee sottili sfarfallano ancora, perché uno scaler spaziale non può inventare campioni che non ha mai avuto; è ciò che lo scaler temporale sistema.
---
Restituisci il movimento da un pass di debug, amplificato perché sia visibile.

{{code}}

A camera ferma l'immagine è nera tranne gli oggetti in movimento. Una panoramica verso destra tinge tutto di rosso, un'inclinazione lo tinge di verde, e le superfici vicine sono più luminose di quelle lontane, perché sullo schermo si spostano di più.
---
Lo scaler presume che i campioni stiano al centro dei pixel, mentre in realtà vengono spostati a ogni frame. Allinea la storia nel modo sbagliato, e l'immagine trema di una frazione di pixel o diventa morbida. L'errore opposto, cioè inviare gli offset senza applicare il jitter alla proiezione, dà un'immagine stabile senza dettaglio in più e senza anti-aliasing.
