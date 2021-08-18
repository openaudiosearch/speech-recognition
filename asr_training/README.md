# ASR Trainingspipelines

In diesem Ordner befinden sich Trainingspipelines für Kaldi (http://github.com/kaldi-asr/kaldi). Sie sind im Kaldi "Recipe" Format organisiert. Derzeit gibt es zwei Recipes:

- s5/: Trainingspipeline, die ein Graphemlexikon verwendet, das von den Wörtern, die sich im Trainingskorpus befinden, erzeugt wird.
- s5_subword/: Trainingspipeline, die ein Subwortlexikon auf Basis von Byte-Pair Encoding verwendet. Das Subwortlexikon wird zunächst auf basis der Wörter bzw. Sätze, die sich im Trainingskorpus befinden, gelernt und dann als Zielwörterbuch verwendet. Der Vorteil dieses Ansatzes ist, dass auch Wörter, die nicht im Lexikon verfügbar sind, auf Basis der Subworteinheiten erkannt werden können.

Die Trainingspipeline befindet sich jeweils im Bash-Skript `run.sh`.
