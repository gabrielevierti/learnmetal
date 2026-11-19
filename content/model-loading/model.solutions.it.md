Chiama il metodo di disegno del modello in un ciclo, ogni volta con una matrice model diversa, moltiplicando la traslazione e la rotazione di ogni copia per la matrice di normalizzazione. I vertex buffer e gli index buffer sono condivisi, quindi dieci copie costano dieci gruppi di draw call e nessuna memoria in più. Per molte copie passa all'instancing.
---
Tieni un dizionario dal percorso del file della texture alla texture caricata, e consultalo prima di caricare. In Swift un `[URL: MTLTexture]` nell'oggetto loader; in C++ una `std::unordered_map<std::string, MTL::Texture*>`. È frequente che un modello usi la stessa immagine in molti materiali, quindi così si riducono sia il tempo di caricamento sia la memoria.
---
Aggiungi `float3 baseColor` agli uniform del fragment, impostalo per ogni submesh a partire dal materiale, collega la texture bianca da 1 × 1 dove non c'è un'immagine, e moltiplica.

{{code}}

Il bianco per il colore dà il colore; un'immagine per un base color bianco dà l'immagine.
