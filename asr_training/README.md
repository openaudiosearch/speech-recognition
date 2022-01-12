# ASR Trainingspipelines

In diesem Ordner befinden sich Trainingspipelines für Kaldi (http://github.com/kaldi-asr/kaldi). Sie sind im Kaldi "Recipe" Format organisiert. Derzeit gibt es zwei Recipes:

- s5/: Trainingspipeline, die ein Graphemlexikon verwendet, das von den Wörtern, die sich im Trainingskorpus befinden, erzeugt wird.
- s5_subword/: Trainingspipeline, die ein Subwortlexikon auf Basis von Byte-Pair Encoding verwendet. Das Subwortlexikon wird zunächst auf basis der Wörter bzw. Sätze, die sich im Trainingskorpus befinden, gelernt und dann als Zielwörterbuch verwendet. Der Vorteil dieses Ansatzes ist, dass auch Wörter, die nicht im Lexikon verfügbar sind, auf Basis der Subworteinheiten erkannt werden können.

Die Trainingspipeline befindet sich jeweils im Bash-Skript `run.sh`.

Um die Trainingspipeline in Docker auszuführen sind folgende Schritte auszuführen:

1. Trainingsdaten herstellen. Zum Testen können die folgenden verwendet werden: https://drive.google.com/file/d/1t0wPL7bAI3GIR8uFymOPxmB1sem4N9Ij/view?usp=sharing

   Die Datei `parl-20210719_segments.tar.gz` herunterladen und entpacken.

2. `docker-compose.yml` im Editor öffnen und die Volumes anpassen. Das erste Volume sollte zum Ordner zeigen, wo die Trainingsdaten entpackt wurden. Die beiden anderen Volumes dienen zum Speichern von Daten und Modellen, die während des Trainings erzeugt werden.

3. `docker-compose build` erzeugt das Docker container image.

3. `docker-compose run asr-training` started die Trainingspipeline.