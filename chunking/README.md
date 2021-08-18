# Chunking Tool

Dieser Ordner beinhaltet Skripte fürs automatische "Chunking", d.h. das automatische Verarbeiten von langen Audio bzw. Videoaufnahmen mit unsauberen Transkripten, um Daten für das Trainieren von Spracherkennungssystemen zu erzeugen. Es kann auch mit Transkripten umgehen, die fehlerhaft sind bzw. wo Teile fehlen.

Die Prozedur wendet ein Kaldi-Spracherkennungsmodell auf die Audiodaten an, wobei ein "biased" Language Model verwendet wird, das von den Transkripten erstellt wurde. Damit wird versucht, automatisch zu überprüfen, ob in den Transkripten enthaltenen Passagen tatsächlich gesprochen werden. Es kann auch Wortwiederholungen und andere Häsitationen, die nicht im Ausgangstranskript enthalten sind, automatisch in das Ausgabetranskript einfügen.