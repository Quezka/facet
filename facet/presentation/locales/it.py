"""Traduzione italiana dell'interfaccia di Facet."""

NAMES: dict[str, list[str]] = {}

# English singular -> (one, other) forms.
PLURALS = {
    "separate part": ("parte separata", "parti separate"),
}

MESSAGES = {
    # ---- window and pages
    "Facet": "Facet",
    "Home": "Home",
    "Viewer": "Visualizzatore",
    "More": "Altro",
    "Start": "Inizia",
    "Recent": "Recenti",
    "Settings": "Impostazioni",
    "Settings…": "Impostazioni…",
    "Close": "Chiudi",
    "All files": "Tutti i file",
    "3D models": "Modelli 3D",
    "PNG pictures": "Immagini PNG",
    "Look at 3D models, and measure the ones that need it.":
        "Guarda i modelli 3D e misura quelli che servono.",
    "Open a model": "Apri un modello",
    "Open a model…": "Apri un modello…",
    "Open…": "Apri…",
    "Opening…": "Apertura…",
    "Opening {name}…": "Apertura di {name}…",
    "STL, OBJ, PLY or 3MF": "STL, OBJ, PLY o 3MF",
    "Sample part": "Pezzo di esempio",
    "A plate with a hole, to try measuring": "Una piastra con un foro, per provare a misurare",
    "Sample shape": "Forma di esempio",
    "A smooth vase, a curved model": "Un vaso liscio, un modello curvo",
    "Drag a file onto the window to open it. In the view: drag to turn, right-drag or Shift-drag to move, wheel to zoom.":
        "Trascina un file sulla finestra per aprirlo. Nella vista: trascina per ruotare, trascina col tasto destro o con Maiusc per spostare, rotella per ingrandire.",
    "No model open.": "Nessun modello aperto.",
    "triangles": "triangoli",
    "Something went wrong: {error}": "Qualcosa è andato storto: {error}",
    "Quit Facet": "Esci da Facet",
    "About Facet": "Informazioni su Facet",
    "A light 3D model viewer, for models you look at and models you measure.":
        "Un visualizzatore 3D leggero, per i modelli da guardare e da misurare.",
    "Free software under the GNU General Public License, version 3 or later.":
        "Software libero con licenza GNU General Public License, versione 3 o successiva.",
    "Restart Facet now": "Riavvia Facet ora",
    "The 3D view couldn't start on this computer.":
        "La vista 3D non è riuscita ad avviarsi su questo computer.",

    # ---- toolbar
    "Solid": "Solido",
    "Edges": "Spigoli",
    "Wire": "Reticolo",
    "Grid": "Griglia",
    "Grid: {step}": "Griglia: {step}",
    "Box size": "Ingombro",
    "Flat view": "Vista piatta",
    "Orthographic view: no perspective, parallel lines stay parallel (O)":
        "Vista ortografica: niente prospettiva, le linee parallele restano parallele (O)",
    "View": "Vista",
    "Front": "Davanti",
    "Back": "Dietro",
    "Left": "Sinistra",
    "Right": "Destra",
    "Top": "Sopra",
    "Bottom": "Sotto",
    "Isometric": "Isometrica",
    "Fit": "Adatta",
    "Fit the model to the window (F)": "Adatta il modello alla finestra (F)",
    "Picture": "Immagine",
    "Save picture…": "Salva immagine…",
    "Save picture": "Salva immagine",
    "Copy picture": "Copia immagine",
    "Previous model in the folder  (Alt+Left)": "Modello precedente nella cartella  (Alt+Sinistra)",
    "Next model in the folder  (Alt+Right)": "Modello successivo nella cartella  (Alt+Destra)",

    # ---- details
    "Details": "Dettagli",
    "Copy these details": "Copia questi dettagli",
    "The model's units": "Unità del modello",
    "Width (X)": "Larghezza (X)",
    "Depth (Y)": "Profondità (Y)",
    "Height (Z)": "Altezza (Z)",
    "Volume": "Volume",
    "Surface area": "Superficie",
    "Weight": "Peso",
    "Centre of mass": "Baricentro",
    "Triangles": "Triangoli",
    "File": "File",
    "Material": "Materiale",
    "The weight is for a solid part; a printed one with infill weighs less.":
        "Il peso è quello di un pezzo pieno; uno stampato con riempimento pesa meno.",

    # ---- mesh check
    "Mesh check": "Controllo della mesh",
    "Open a model to check it.": "Apri un modello per controllarlo.",
    "Checking the mesh…": "Controllo della mesh…",
    "This model is too big to check its mesh.": "Questo modello è troppo grande per controllarne la mesh.",
    "Watertight: a closed solid, ready to print.": "A tenuta stagna: un solido chiuso, pronto da stampare.",
    "{edges} open edges: the surface has holes or gaps.": "{edges} spigoli aperti: la superficie ha buchi o fessure.",
    "{edges} edges shared by more than two faces.": "{edges} spigoli condivisi da più di due facce.",
    "The faces point inwards (inside out).": "Le facce guardano verso l'interno (rovesciato).",
    "{n} triangles with no area.": "{n} triangoli senza area.",
    "{n} vertices": "{n} vertici",

    # ---- measuring
    "Measure": "Misura",
    "Off": "No",
    "Distance": "Distanza",
    "Angle": "Angolo",
    "Hole": "Foro",
    "Supplement": "Supplementare",
    "Diameter": "Diametro",
    "Radius": "Raggio",
    "Snap to corners and edges": "Aggancia a vertici e spigoli",
    "Pick a tool, then click points on the model. Angle: the corner is the second point. Hole: three points around it.":
        "Scegli uno strumento, poi clicca punti sul modello. Angolo: il vertice è il secondo punto. Foro: tre punti lungo il bordo.",
    "Copy": "Copia",
    "Remove": "Rimuovi",
    "Clear": "Svuota",
    "Click the first point": "Clicca il primo punto",
    "Click the second point": "Clicca il secondo punto",
    "Click a point on the first side": "Clicca un punto sul primo lato",
    "Click the corner of the angle": "Clicca il vertice dell'angolo",
    "Click a point on the second side": "Clicca un punto sul secondo lato",
    "Click a point on the hole or curve": "Clicca un punto sul foro o sulla curva",
    "Click a second point on it": "Clicca un secondo punto",
    "Click a third point on it": "Clicca un terzo punto",
    "Pick three different points.": "Scegli tre punti diversi.",
    "The three points are in a line: pick points around the hole.":
        "I tre punti sono allineati: scegli punti attorno al foro.",
    "That point isn't on the model.": "Quel punto non è sul modello.",

    # ---- section and look
    "Section": "Sezione",
    "Cut the model with a plane": "Taglia il modello con un piano",
    "Keep the other side": "Tieni l'altro lato",
    "Look": "Aspetto",
    "Smooth shading": "Ombreggiatura morbida",
    "Use the colours stored in the file": "Usa i colori salvati nel file",
    "Clay": "Argilla",
    "Indigo": "Indaco",
    "Amber": "Ambra",
    "Mint": "Menta",
    "Rose": "Rosa",
    "Steel": "Acciaio",
    "White": "Bianco",

    # ---- settings
    "Appearance": "Aspetto",
    "System": "Sistema",
    "Light": "Chiaro",
    "Dark": "Scuro",
    "High contrast (black and white, thick lines)": "Alto contrasto (bianco e nero, linee spesse)",
    "Numbers": "Numeri",
    "Decimal places in measurements": "Cifre decimali nelle misure",
    "The units (mm, cm, m, inches) are chosen next to the model.":
        "Le unità (mm, cm, m, pollici) si scelgono accanto al modello.",
    "Language": "Lingua",
    "Interface language": "Lingua dell'interfaccia",
    "Interface size": "Dimensione dell'interfaccia",
    "Automatic": "Automatica",
    "Applies after a restart. Automatic is a comfortable, slightly larger size.":
        "Si applica dopo un riavvio. Automatica è una dimensione comoda, un po' più grande.",
    "Updates": "Aggiornamenti",
    "Check for new versions once a day": "Cerca nuove versioni una volta al giorno",
    "Check now": "Controlla ora",
    "You have version {version}.": "Hai la versione {version}.",

    # ---- updates
    "Check for updates…": "Cerca aggiornamenti…",
    "Update available": "Aggiornamento disponibile",
    "Facet {version} is available": "Facet {version} è disponibile",
    "You have {version}. Here's what's new:": "Hai la {version}. Ecco le novità:",
    "No release notes.": "Nessuna nota di versione.",
    "Update now": "Aggiorna ora",
    "Later": "Più tardi",
    "Skip this version": "Salta questa versione",
    "Open download page": "Apri la pagina di download",
    "Downloading…": "Download…",
    "Downloading… {done} of {total} MB": "Download… {done} di {total} MB",
    "Installing… your system may ask for your password.":
        "Installazione… il sistema potrebbe chiedere la password.",
    "No updates": "Nessun aggiornamento",
    "You have the latest version of Facet ({version}).": "Hai l'ultima versione di Facet ({version}).",
    "Couldn't check for updates": "Impossibile cercare aggiornamenti",
    "Can't reach GitHub to check for updates. Check your internet connection.":
        "Impossibile raggiungere GitHub per cercare aggiornamenti. Controlla la connessione a internet.",
    "GitHub is limiting update checks right now: try again in an hour.":
        "GitHub sta limitando i controlli di aggiornamento: riprova tra un'ora.",
    "GitHub sent an answer Facet doesn't understand.": "GitHub ha inviato una risposta che Facet non capisce.",
    "There's no download for this computer in that release.":
        "In quella versione non c'è un download per questo computer.",
    "The download didn't finish. Check your internet connection and try again.":
        "Il download non è terminato. Controlla la connessione a internet e riprova.",
    "The download was damaged (its checksum doesn't match), so it wasn't installed. Try again.":
        "Il download era danneggiato (il checksum non corrisponde), quindi non è stato installato. Riprova.",
    "This copy of Facet can't update itself (for example when it runs from source). Download the new version from GitHub.":
        "Questa copia di Facet non può aggiornarsi da sola (ad esempio se eseguita dai sorgenti). Scarica la nuova versione da GitHub.",
    "This copy of Facet can't update itself.": "Questa copia di Facet non può aggiornarsi da sola.",
    "Couldn't start the installer.": "Impossibile avviare l'installatore.",
    "Installing was cancelled.": "L'installazione è stata annullata.",

    # ---- errors from the use cases
    "No model is open.": "Nessun modello è aperto.",
    "Facet can't open this kind of file.": "Facet non può aprire questo tipo di file.",
    "The file couldn't be read.": "Impossibile leggere il file.",
    "This file is damaged.": "Questo file è danneggiato.",
    "This file has no triangles in it.": "Questo file non contiene triangoli.",
    "This doesn't look like an STL file.": "Questo non sembra un file STL.",
    "This STL file is damaged or empty.": "Questo file STL è danneggiato o vuoto.",
    "This OBJ file is damaged.": "Questo file OBJ è danneggiato.",
    "This OBJ file has no faces.": "Questo file OBJ non ha facce.",
    "This doesn't look like a PLY file.": "Questo non sembra un file PLY.",
    "This PLY file is damaged.": "Questo file PLY è danneggiato.",
    "This PLY file has no faces.": "Questo file PLY non ha facce.",
    "This doesn't look like a 3MF file.": "Questo non sembra un file 3MF.",
    "This 3MF file is damaged.": "Questo file 3MF è danneggiato.",
    "This 3MF file has no model in it.": "Questo file 3MF non contiene un modello.",
    "This 3MF file has no mesh in it.": "Questo file 3MF non contiene una mesh.",
}
