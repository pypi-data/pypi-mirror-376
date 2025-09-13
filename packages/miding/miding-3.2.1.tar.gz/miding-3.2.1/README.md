# Miding  _3.2.1_

This program names '**miding**', an abbreviation of '**Midi Neuronal Generator**', 
which aims to generate listenable midi sequences, attempting to create fair scores.

Sincerely thanks for _**keras**_, the neuronal network model we have applied.
In this program, the model construction is two GRU layer and a Dense layer with the activation Softmax.
### Download

Here is our website:
* https://github.com/JerrySkywolf/miding

This package could also be downloaded through PyPi by:

`pip install miding`

View at the webpage
* https://pypi.org/project/miding

### How to use the model?

First, **COPY** the model files (*.keras) from our package to your programme path **by calling 'resources.check()'** after importing the package,
which is extremely important!

``from miding import Predict, Seed, resources``
``resources.check(resources.absolute_path(__file__))``

And then, for example, you could use a random seed:

``s = Seed(midi_file='example_seed.mid')``
``Predict(seed=s.get_seed(),epoch=128, model_version=1751770203)``



 