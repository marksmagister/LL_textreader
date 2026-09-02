/** The interface, in English or German.
 *
 * A dict of strings and a lookup, not a library: there is one screenful of UI
 * text and a translation framework would be more machinery than the thing it
 * translates.
 *
 * Two rules make it work. **English is the source of truth** — `Strings` is its
 * type, so a missing or mistyped German entry is a compile error rather than a
 * blank button. And **the locale is module state, not a prop**: `t` is imported
 * where it is used, and changing the language re-renders from the top, which is
 * enough because nothing here is memoised.
 *
 * The interface language is not the language you are reading (`lang.ts`) and not
 * the language you translate into. 0012 is emphatic about that: a German speaker
 * reading French may well want English glosses.
 *
 * **English is the default and stays the default**, on the maintainer's
 * instruction. German is a choice, never an inference from the browser.
 */

const en = {
  // --------------------------------------------------------------- getting about
  'nav.library': '← library',
  'nav.vocabulary': 'vocabulary',
  'nav.legend': 'legend',
  'nav.settings': 'settings',
  'app.paletteHint': 'press / for commands',
  'app.themeToLight': 'light mode',
  'app.themeToDark': 'dark mode',
  'app.themeTitle': 'light or dark',
  'palette.placeholder': 'command…',
  'cmd.library': 'library — import or open a text',
  'cmd.vocab': 'vocabulary — everything you know',
  'cmd.legend': 'legend — what the colours and keys mean',
  'cmd.settings': 'settings — your languages, and the interface',
  'cmd.theme': 'dark / light — switch the theme',
  'cmd.system': 'follow the system theme',

  // ------------------------------------------------------------------- languages
  'lang.yours': 'Your languages',
  'lang.available': 'Also available',
  'lang.pick': 'the language you are reading',
  'lang.fr': 'French',
  'lang.ru': 'Russian',
  'lang.it': 'Italian',
  'lang.nl': 'Dutch',
  'lang.en': 'English',
  'lang.de': 'German',

  // ---------------------------------------------------------------------- undo
  'undo.marked': (n: number) => `Marked ${n} words known.`,
  'undo.undo': 'undo',
  'undo.dismiss': 'dismiss',

  // -------------------------------------------------------------------- import
  'import.urlPlaceholder': 'paste the address of an article…',
  'import.fetch': 'fetch',
  'import.titlePlaceholder': 'title (optional)',
  'import.textPlaceholder': (language: string) =>
    `Paste ${language} text, or choose a .txt file`,
  'import.file': 'choose a .txt file',
  'import.import': 'Import',
  'import.reading': 'reading the page…',
  'import.check': 'check it over, then import',
  'import.importing': 'importing — lemmatising, this takes a moment…',
  'import.added': (title: string) => `added “${title}”`,

  // ------------------------------------------------------------------ starters
  'starters.add': (n: number) => `add ${n} texts to start with`,
  'starters.hint': 'short texts written for this reader, so there is something to read',
  'starters.adding': 'adding…',
  'starters.added': (n: number) => `added ${n} texts — they are in the list below`,

  // ------------------------------------------------------------------- library
  'list.empty': 'Nothing here yet. Import something above.',
  'list.emptyLang': (language: string) => `Nothing in ${language} yet. Import something above.`,
  'list.continue': 'Continue',
  'list.readShare': 'read',
  'list.search': 'search titles…',
  'list.title': 'title',
  'list.youKnow': 'you know',
  'list.sortRecent': 'last read',
  'list.sortTitle': 'title',
  'list.sortKnown': 'you know',
  'list.sortLength': 'length',
  'list.words': (n: number) => `${n} words`,
  'list.known': (n: number) => `${n} you know`,
  'list.learning': (n: number) => `${n} learning`,
  'list.new': (n: number) => `${n} never seen`,
  'list.finished': 'finished',
  'list.through': (pct: string) => `${pct} of the way through`,
  'list.notStarted': 'not started',
  'list.usedAgo': (ago: string) => `used ${ago}`,
  'list.neverOpened': 'never opened',
  'list.parts': (n: number) => `${n} parts`,
  'list.partsRead': (n: number) => `${n} read`,
  'list.collectionPlaceholder': 'collection name — blank to take it out',
  'list.deleteConfirm': 'delete?',
  'list.putInCollection': 'put in a collection',
  'list.remove': 'remove',
  'list.noMatch': (q: string) => `Nothing matches “${q}”.`,
  'list.done': 'done',

  // ---------------------------------------------------------------------- time
  'time.today': 'today',
  'time.yesterday': 'yesterday',
  'time.daysAgo': (n: number) => `${n} days ago`,
  'time.daysAgoShort': (n: number) => `${n}d ago`,
  'time.never': 'never met',

  // -------------------------------------------------------------------- reader
  'reader.pageOf': (page: number, total: number) => `page ${page} of ${total}`,
  'reader.newOf': (n: number, total: number) => `${n} new of ${total} words`,
  'reader.back': '‹ back',
  'reader.backTitle': 'the previous page',
  'reader.translateTitle': 'a translation under each sentence',
  'reader.markOnClick': 'click = learning',
  'reader.markOnClickTitle': 'while on, clicking a blue word marks it as learning',
  'reader.markPage': 'Mark page known',
  'reader.markPageTitle': '⇧ K — clears the blue and answers the underlined',
  'reader.next': 'Next page ›',
  'reader.finish': 'Finish',
  'reader.nextTitle': 'turn the page and record what you met',
  'reader.starting': 'starting the translator — the first page of a session takes a minute',
  'reader.translating': 'translating this page…',
  'reader.noTranslator': 'translation not installed — uv sync --extra translate',
  'reader.hear': 'hear it',
  'reader.wrongWord': 'wrong word?',
  'reader.undoOverride': 'undo override',
  'reader.noEntry': 'no dictionary entry',
  'reader.fixPlaceholder': (surface: string) =>
    `correct lemma for "${surface}" — blank to detach it`,
  'reader.save': 'save',
  'reader.cancel': 'cancel',
  'reader.notePlaceholder': 'your own note — saved when you click away, ⌘↵ saves as learning',
  'reader.learning': '1 learning',
  'reader.known': 'k known',
  'reader.ignore': 'i ignore',
  'reader.esc': 'esc',
  'reader.metOften': 'met this often — do you know it now?',

  // ---------------------------------------------------------------- vocabulary
  'vocab.title': 'Vocabulary',
  'vocab.summary': (total: number, known: number) => `${total} words · ${known} known`,
  'vocab.all': 'all',
  'vocab.new': 'new',
  'vocab.learning': 'learning',
  'vocab.known': 'known',
  'vocab.ignored': 'ignored',
  'vocab.startsWith': 'starts with…',
  'vocab.sort': 'sort:',
  'vocab.sortRecent': 'last seen',
  'vocab.sortStale': 'longest unseen',
  'vocab.sortAlpha': 'a–z',
  'vocab.sortForms': 'most forms',
  'vocab.export': (scope: string) => `export ${scope}:`,
  'vocab.selected': (n: number) => `${n} selected`,
  'vocab.allOf': (n: number) => `all ${n}`,
  'vocab.shown': (n: number) => `${n} shown`,
  'vocab.anki': 'Anki deck',
  'vocab.clearSelection': 'clear selection',
  'vocab.empty': 'Nothing here yet.',
  'vocab.seen': (n: number) => `seen ${n}×`,
  'vocab.noForms': 'no forms met yet',
  'vocab.doYouKnow': 'do you know it?',
  'vocab.select': (lemma: string) => `select ${lemma}`,

  // -------------------------------------------------------------------- report
  'report.tab': "something's wrong",
  'report.tabTitle': 'report a problem',
  'report.placeholder': 'What went wrong? Where you are is sent with it.',
  'report.send': 'send',
  'report.sending': 'sending…',
  'report.sent': 'thank you',
  'report.close': 'close',
  'report.failed': 'could not send',

  // ------------------------------------------------------------------ settings
  'settings.title': 'Settings',
  'settings.study': 'Languages you are learning',
  'settings.studyHint':
    'These are the ones in the header dropdown. The language you are reading sets what an import is read as, which words the vocabulary page shows, and what the library lists.',
  'settings.reading': 'reading',
  'settings.read': 'read this',
  'settings.drop': 'not learning this',
  'settings.take': 'start learning this',
  'settings.available': 'Available on this server',
  'settings.availableHint':
    'Everything the server has a model for. Adding one puts it in your list; it is not a download.',
  'settings.allYours': 'You have all of them.',
  'settings.interface': 'Interface language',
  'settings.interfaceHint':
    'The buttons and labels — not what you are reading, and not what you translate into.',
  'settings.grammar': (locale: string) =>
    `Grammar is named in ${locale}: the language you are reading when this reader has the words for it, otherwise the language of the interface.`,
  'settings.missing': (language: string) =>
    `The model for ${language} is not installed on this server. Importing will fail until it is: ./scripts/setup-models.sh`,

  // -------------------------------------------------------------------- legend
  'legend.title': 'What the colours mean',
  'legend.new': 'New. You have never said anything about this word.',
  'legend.novelForm': 'You know this word. This shape of it is new to you.',
  'legend.learning': 'You are learning it.',
  'legend.review': 'You have met this a lot now. Do you know it yet?',
  'legend.known': 'Known. Nothing to do.',
  'legend.blueNote':
    'Blue always means the word wants something from you. Filled in, you have never judged it. Dashed, you know the word but not this shape of it. Underlined, you have met it often enough that it is time you decided.',
  'legend.loopTitle': 'The loop',
  'legend.loopNote':
    'That is the whole thing. You never hunt for words; Tab finds the next one that is not plain — the blue, the yellow you are still learning, the shapes you have not met and the ones underlined because it is time you decided. Do not be shy with ⇧ K — clearing a page you can mostly read is the point, not cheating.',
  'legend.keysTitle': 'Keys',
  'legend.buttonsTitle': 'Buttons',
  'legend.surprisesTitle': 'Two things that surprise people',
  'legend.surprise1a': 'Marking a word marks ',
  'legend.surprise1b': 'the word',
  'legend.surprise1c': ', not the spelling. Say you know ',
  'legend.surprise1d':
    ' and every form of it changes — except ones you have not actually met, which get the underline.',
  'legend.surprise2':
    'A page counts once. Reading it again does not move anything on, because what makes meeting a word again useful is the gap in between.',
  'key.tab': 'jump to the next word that is not plain — blue, yellow or dashed',
  'key.shiftTab': 'jump back',
  'key.1': "I'm learning this",
  'key.k': 'I know this',
  'key.i': 'ignore it — names, numbers',
  'key.shiftK': 'everything unresolved on this page → known, and stay here',
  'key.sentence': 'move one sentence',
  'key.enter': 'write your own note',
  'key.esc': 'back to the text',
  'key.o': 'the word underneath is wrong',
  'key.space': 'hear the sentence',
  'key.slash': 'go somewhere else',
  'btn.translate': 'put a translation under each sentence',
  'btn.markOnClick': 'while on, clicking a blue word marks it — good for a fast pass',
  'btn.markPage': 'clears the blue and answers the underlined; you stay on the page',
  'btn.next': 'turn the page and record what you met',
  'btn.undo': 'appears after a bulk change; takes it back',
  'btn.report': 'tell me about it — bottom right, on every page',
}

type Strings = typeof en

// German has to match English exactly, key for key and argument for argument.
// That is the whole reason `Strings` is a type rather than a loose Record: a
// forgotten string is a build failure here, not a blank button in front of a
// reader who cannot read the other language.
const de: Strings = {
  'nav.library': '← Bibliothek',
  'nav.vocabulary': 'Wortschatz',
  'nav.legend': 'Legende',
  'nav.settings': 'Einstellungen',
  'app.paletteHint': '/ drücken für Befehle',
  'app.themeToLight': 'heller Modus',
  'app.themeToDark': 'dunkler Modus',
  'app.themeTitle': 'hell oder dunkel',
  'palette.placeholder': 'Befehl…',
  'cmd.library': 'Bibliothek — Text importieren oder öffnen',
  'cmd.vocab': 'Wortschatz — alles, was du kennst',
  'cmd.legend': 'Legende — was die Farben und Tasten bedeuten',
  'cmd.settings': 'Einstellungen — deine Sprachen und die Oberfläche',
  'cmd.theme': 'dunkel / hell — Darstellung wechseln',
  'cmd.system': 'der Systemeinstellung folgen',

  'lang.yours': 'Deine Sprachen',
  'lang.available': 'Ebenfalls verfügbar',
  'lang.pick': 'die Sprache, die du liest',
  'lang.fr': 'Französisch',
  'lang.ru': 'Russisch',
  'lang.it': 'Italienisch',
  'lang.nl': 'Niederländisch',
  'lang.en': 'Englisch',
  'lang.de': 'Deutsch',

  'undo.marked': (n) => `${n} Wörter als bekannt markiert.`,
  'undo.undo': 'rückgängig',
  'undo.dismiss': 'schließen',

  'import.urlPlaceholder': 'Adresse eines Artikels einfügen…',
  'import.fetch': 'holen',
  'import.titlePlaceholder': 'Titel (optional)',
  'import.textPlaceholder': (language) =>
    `Text auf ${language} einfügen oder eine .txt-Datei wählen`,
  'import.file': '.txt-Datei wählen',
  'import.import': 'Importieren',
  'import.reading': 'Seite wird gelesen…',
  'import.check': 'prüfen, dann importieren',
  'import.importing': 'wird importiert — Lemmatisierung, das dauert einen Moment…',
  'import.added': (title) => `„${title}“ hinzugefügt`,

  'starters.add': (n) => `${n} Texte zum Anfangen hinzufügen`,
  'starters.hint': 'kurze Texte für diesen Reader geschrieben, damit es etwas zu lesen gibt',
  'starters.adding': 'wird hinzugefügt…',
  'starters.added': (n) => `${n} Texte hinzugefügt — sie stehen unten in der Liste`,

  'list.empty': 'Noch nichts da. Importiere oben etwas.',
  'list.emptyLang': (language) => `Noch nichts auf ${language}. Importiere oben etwas.`,
  'list.continue': 'Weiterlesen',
  'list.readShare': 'gelesen',
  'list.search': 'Titel durchsuchen…',
  'list.title': 'Titel',
  'list.youKnow': 'du kennst',
  'list.sortRecent': 'zuletzt gelesen',
  'list.sortTitle': 'Titel',
  'list.sortKnown': 'du kennst',
  'list.sortLength': 'Länge',
  'list.words': (n) => `${n} Wörter`,
  'list.known': (n) => `${n} kennst du`,
  'list.learning': (n) => `${n} am Lernen`,
  'list.new': (n) => `${n} nie gesehen`,
  'list.finished': 'fertig gelesen',
  'list.through': (pct) => `${pct} geschafft`,
  'list.notStarted': 'nicht begonnen',
  'list.usedAgo': (ago) => `benutzt ${ago}`,
  'list.neverOpened': 'nie geöffnet',
  'list.parts': (n) => `${n} Teile`,
  'list.partsRead': (n) => `${n} gelesen`,
  'list.collectionPlaceholder': 'Name der Sammlung — leer heißt: heraus damit',
  'list.deleteConfirm': 'löschen?',
  'list.putInCollection': 'in eine Sammlung legen',
  'list.remove': 'entfernen',
  'list.noMatch': (q) => `Nichts passt zu „${q}“.`,
  'list.done': 'fertig',

  'time.today': 'heute',
  'time.yesterday': 'gestern',
  'time.daysAgo': (n) => `vor ${n} Tagen`,
  'time.daysAgoShort': (n) => `vor ${n} T.`,
  'time.never': 'nie begegnet',

  'reader.pageOf': (page, total) => `Seite ${page} von ${total}`,
  'reader.newOf': (n, total) => `${n} neu von ${total} Wörtern`,
  'reader.back': '‹ zurück',
  'reader.backTitle': 'die vorherige Seite',
  'reader.translateTitle': 'eine Übersetzung unter jedem Satz',
  'reader.markOnClick': 'Klick = am Lernen',
  'reader.markOnClickTitle': 'solange an: ein Klick auf ein blaues Wort setzt es auf „am Lernen“',
  'reader.markPage': 'Seite als bekannt',
  'reader.markPageTitle': '⇧ K — räumt das Blau ab und beantwortet das Unterstrichene',
  'reader.next': 'Nächste Seite ›',
  'reader.finish': 'Fertig',
  'reader.nextTitle': 'umblättern und festhalten, was dir begegnet ist',
  'reader.starting': 'die Übersetzung startet — die erste Seite einer Sitzung dauert eine Minute',
  'reader.translating': 'diese Seite wird übersetzt…',
  'reader.noTranslator': 'Übersetzung nicht installiert — uv sync --extra translate',
  'reader.hear': 'anhören',
  'reader.wrongWord': 'falsches Wort?',
  'reader.undoOverride': 'Korrektur zurücknehmen',
  'reader.noEntry': 'kein Wörterbucheintrag',
  'reader.fixPlaceholder': (surface) =>
    `richtiges Grundwort für „${surface}“ — leer lassen, um es zu lösen`,
  'reader.save': 'speichern',
  'reader.cancel': 'abbrechen',
  'reader.notePlaceholder':
    'deine eigene Notiz — gespeichert, wenn du wegklickst; ⌘↵ speichert als „am Lernen“',
  'reader.learning': '1 am Lernen',
  'reader.known': 'k bekannt',
  'reader.ignore': 'i ignorieren',
  'reader.esc': 'esc',
  'reader.metOften': 'oft begegnet — kennst du es jetzt?',

  'vocab.title': 'Wortschatz',
  'vocab.summary': (total, known) => `${total} Wörter · ${known} bekannt`,
  'vocab.all': 'alle',
  'vocab.new': 'neu',
  'vocab.learning': 'am Lernen',
  'vocab.known': 'bekannt',
  'vocab.ignored': 'ignoriert',
  'vocab.startsWith': 'beginnt mit…',
  'vocab.sort': 'sortieren:',
  'vocab.sortRecent': 'zuletzt gesehen',
  'vocab.sortStale': 'am längsten nicht gesehen',
  'vocab.sortAlpha': 'a–z',
  'vocab.sortForms': 'meiste Formen',
  'vocab.export': (scope) => `${scope} exportieren:`,
  'vocab.selected': (n) => `${n} ausgewählt`,
  'vocab.allOf': (n) => `alle ${n}`,
  'vocab.shown': (n) => `${n} angezeigt`,
  'vocab.anki': 'Anki-Stapel',
  'vocab.clearSelection': 'Auswahl aufheben',
  'vocab.empty': 'Noch nichts da.',
  'vocab.seen': (n) => `${n}× gesehen`,
  'vocab.noForms': 'noch keine Formen begegnet',
  'vocab.doYouKnow': 'kennst du es?',
  'vocab.select': (lemma) => `${lemma} auswählen`,

  'report.tab': 'etwas stimmt nicht',
  'report.tabTitle': 'ein Problem melden',
  'report.placeholder': 'Was ist schiefgegangen? Wo du gerade bist, wird mitgeschickt.',
  'report.send': 'senden',
  'report.sending': 'wird gesendet…',
  'report.sent': 'danke',
  'report.close': 'schließen',
  'report.failed': 'konnte nicht gesendet werden',

  'settings.title': 'Einstellungen',
  'settings.study': 'Sprachen, die du lernst',
  'settings.studyHint':
    'Diese stehen im Menü oben. Die Sprache, die du liest, bestimmt, als was ein Import gelesen wird, welche Wörter im Wortschatz stehen und was die Bibliothek zeigt.',
  'settings.reading': 'wird gelesen',
  'settings.read': 'diese lesen',
  'settings.drop': 'lerne ich nicht mehr',
  'settings.take': 'diese dazunehmen',
  'settings.available': 'Auf diesem Server verfügbar',
  'settings.availableHint':
    'Alles, wofür der Server ein Modell hat. Etwas dazuzunehmen heißt nicht, etwas herunterzuladen.',
  'settings.allYours': 'Du hast schon alle.',
  'settings.interface': 'Sprache der Oberfläche',
  'settings.interfaceHint':
    'Die Schaltflächen und Beschriftungen — nicht das, was du liest, und nicht das, wohin übersetzt wird.',
  'settings.grammar': (locale) =>
    `Die Grammatik wird auf ${locale} benannt: in der Sprache, die du liest, sofern dieser Reader die Wörter dafür hat, sonst in der Sprache der Oberfläche.`,
  'settings.missing': (language) =>
    `Das Modell für ${language} ist auf diesem Server nicht installiert. Importieren schlägt fehl, bis es da ist: ./scripts/setup-models.sh`,

  'legend.title': 'Was die Farben bedeuten',
  'legend.new': 'Neu. Zu diesem Wort hast du noch nie etwas gesagt.',
  'legend.novelForm': 'Du kennst dieses Wort. Diese Form davon ist neu für dich.',
  'legend.learning': 'Du lernst es gerade.',
  'legend.review': 'Das ist dir schon oft begegnet. Kennst du es inzwischen?',
  'legend.known': 'Bekannt. Nichts zu tun.',
  'legend.blueNote':
    'Blau heißt immer: dieses Wort will etwas von dir. Ausgefüllt — du hast noch nie darüber entschieden. Gestrichelt — du kennst das Wort, aber nicht diese Form. Unterstrichen — es ist dir oft genug begegnet, dass du dich entscheiden solltest.',
  'legend.loopTitle': 'Die Schleife',
  'legend.loopNote':
    'Das ist alles. Du suchst nie nach Wörtern; Tab findet das nächste, das nicht schlicht ist — das Blaue, das Gelbe, das du noch lernst, die Formen, die dir noch nicht begegnet sind, und die Unterstrichenen, bei denen es Zeit für eine Entscheidung ist. Sei nicht zu sparsam mit ⇧ K — eine Seite abzuräumen, die du größtenteils lesen kannst, ist der Sinn der Sache und kein Schummeln.',
  'legend.keysTitle': 'Tasten',
  'legend.buttonsTitle': 'Schaltflächen',
  'legend.surprisesTitle': 'Zwei Dinge, die überraschen',
  'legend.surprise1a': 'Ein Wort zu markieren markiert ',
  'legend.surprise1b': 'das Wort',
  'legend.surprise1c': ', nicht die Schreibweise. Sag, dass du ',
  'legend.surprise1d':
    ' kennst, und jede Form davon ändert sich — außer denen, die dir noch nicht wirklich begegnet sind; die bekommen die Unterstreichung.',
  'legend.surprise2':
    'Eine Seite zählt einmal. Sie noch einmal zu lesen bringt nichts weiter, denn was ein Wiedersehen mit einem Wort nützlich macht, ist der Abstand dazwischen.',
  'key.tab': 'zum nächsten Wort springen, das nicht schlicht ist — blau, gelb oder gestrichelt',
  'key.shiftTab': 'zurückspringen',
  'key.1': 'das lerne ich gerade',
  'key.k': 'das kenne ich',
  'key.i': 'ignorieren — Namen, Zahlen',
  'key.shiftK': 'alles Offene auf dieser Seite → bekannt, und hier bleiben',
  'key.sentence': 'einen Satz weiter',
  'key.enter': 'eigene Notiz schreiben',
  'key.esc': 'zurück in den Text',
  'key.o': 'das Wort darunter stimmt nicht',
  'key.space': 'den Satz anhören',
  'key.slash': 'woanders hin',
  'btn.translate': 'eine Übersetzung unter jeden Satz setzen',
  'btn.markOnClick': 'solange an: ein Klick auf ein blaues Wort markiert es — gut für einen schnellen Durchgang',
  'btn.markPage': 'räumt das Blau ab und beantwortet das Unterstrichene; du bleibst auf der Seite',
  'btn.next': 'umblättern und festhalten, was dir begegnet ist',
  'btn.undo': 'erscheint nach einer Sammeländerung; nimmt sie zurück',
  'btn.report': 'sag mir Bescheid — unten rechts, auf jeder Seite',
}

const TABLES: Record<string, Strings> = { en, de }

/** The languages the interface itself is available in. */
export const UI_LOCALES = Object.keys(TABLES)

const KEY = 'll_textreader_ui'

function initial(): string {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved && TABLES[saved]) return saved
  } catch {
    // private windows and blocked site data both throw
  }
  // English until someone chooses otherwise, on the maintainer's instruction.
  // It was briefly taken from `navigator.language`, which would have handed a
  // German browser a German interface without being asked — convenient, and the
  // wrong default for a project whose one interface language is English.
  return 'en'
}

let current = initial()

export function uiLocale(): string {
  return current
}

export function setUiLocale(locale: string) {
  current = TABLES[locale] ? locale : 'en'
  try {
    localStorage.setItem(KEY, current)
  } catch {
    // failing to remember the choice is no reason to ignore it
  }
}

/** One string, in whatever the interface language is.
 *
 * Returns the entry itself, so a plain string is used directly and one that
 * takes values is called: `t('undo.marked')(3)`. That is a little blunt at the
 * call site and it is what keeps the arguments type-checked per string.
 */
export function t<K extends keyof Strings>(key: K): Strings[K] {
  return (TABLES[current] ?? en)[key]
}

/** A language's name, in the interface language. Falls back to the code, so a
 *  server offering something this build has never heard of still lists it. */
export function languageName(code: string): string {
  const key = `lang.${code}` as keyof Strings
  const name = (TABLES[current] ?? en)[key]
  return typeof name === 'string' ? name : code
}
