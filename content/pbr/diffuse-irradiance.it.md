# Irradianza diffusa

Le luci puntiformi sono solo una parte della luce di una scena. La maggior parte di ciò che arriva su una superficie è luce d'ambiente: il cielo, il suolo, una parete vicina. L'**image-based lighting** (IBL) tratta un'immagine dell'intero ambiente come un'unica grande sorgente di luce, così gli oggetti sembrano appartenere a ciò che li circonda.

L'equazione della riflettanza si divide in modo pulito in un integrale diffuse e in uno specular. Questo capitolo si occupa della metà diffuse.

## L'integrale diffuse

Per il termine lambertiano la BRDF è una costante, quindi esce dall'integrale:

{{code}}

L'integrale che resta dipende solo dalla normale `n`. È la luce totale che arriva sull'emisfero intorno a `n`, pesata con il coseno. Possiamo **precalcolarlo** per ogni normale possibile e salvare i risultati in una cubemap, la **irradiance map**. Al momento del rendering la luce diffusa d'ambiente è una sola lettura di texture con la normale della superficie.

## Environment map HDR

Le immagini d'ambiente devono essere HDR, perché il sole è migliaia di volte più luminoso del cielo che lo circonda. Di solito vengono distribuite come immagini **equirettangolari**, un panorama 2:1, in formato Radiance `.hdr` o OpenEXR. Poly Haven ne ha una grande raccolta gratuita.

Image I/O decodifica entrambi i formati. Disegna l'immagine in una bitmap in virgola mobile e caricala:

{{code}}

## Dal panorama alla cubemap

Una cubemap è più facile da leggere e da convolvere di un panorama, quindi converti una volta sola al caricamento. Disegna un cubo unitario in ognuna delle sei facce di una texture a cubo `.rgba16Float`, usando le matrici sinistrorse delle facce del capitolo [Cubemap](../advanced-metal/cubemaps.html), con la camera nell'origine:

{{code}}

{{code}}

Disegna il cubo con il culling disattivato, perché la camera sta al suo interno. Crea il cubo dell'ambiente con le mipmap e chiama poi `generateMipmaps(for:)` con un blit encoder; serviranno al prossimo capitolo. Una dimensione di 512 o 1024 per faccia basta e avanza. Ora puoi mostrare l'ambiente come skybox, con il tone mapping applicato insieme a tutto il resto.

## Convolvere la irradiance map

Per ogni direzione della cubemap di irradianza ci serve la media dell'ambiente, pesata con il coseno, sull'emisfero intorno a essa. L'integrale si approssima campionando l'emisfero su una griglia regolare di coordinate sferiche:

{{code}}

`cos(theta)` è il fattore coseno dell'integrale, e `sin(theta)` compensa il fatto che i punti di campionamento si addensano verso il polo dell'emisfero. Leggere un livello di mip più basso dell'ambiente (qui il livello 3) elimina i puntini luminosi che un sole piccolo e intenso altrimenti provocherebbe.

Disegna il risultato in un piccolo cubo con `renderToCube`. La irradiance map è molto sfocata per natura, quindi bastano **32 × 32** per faccia. Si calcola una volta sola, al caricamento.

## Usarla

Nello shader PBR sostituisci il termine ambient costante:

{{code}}

{{code}}

La luce d'ambiente arriva da tutte le direzioni, quindi non esiste un unico vettore halfway per il termine di Fresnel. Usiamo l'angolo tra la normale e la direzione di vista, e una variante di Fresnel-Schlick che tiene conto della roughness, così le superfici ruvide non prendono bordi luminosi.

Ora le sfere raccolgono in alto il blu del cielo e in basso il colore del suolo, e finalmente stanno dentro il loro ambiente. I metalli appaiono neri nelle zone non illuminate, perché non hanno termine diffuse. Aspettano i riflessi speculari, che arrivano subito dopo.

## Alternative

- Le **armoniche sferiche** rappresentano l'irradianza di un ambiente con appena nove colori, tanto varia dolcemente. Model I/O le sa calcolare (`MDLLightProbe`), e valutarle nello shader costa meno di una lettura da cubemap.
- `MDLTexture.irradianceTextureCube(with:name:dimensions:)` genera al posto tuo una cubemap di irradianza da una cubemap d'ambiente. Scrivere una volta la convoluzione da te resta il modo migliore di capire che cosa contiene la mappa.
