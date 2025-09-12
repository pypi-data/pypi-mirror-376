# Reader Raman

Pacchetto per lettura e visualizzazione delle misure salvate da software per sensore DTS Raman.

## Installazione

Tramite `pip`:

```bash
pip install readerraman
```

## Utilizzo

Per prima cosa è necessario caricare il necessario dai due moduli di lettura e visualizzazione:

```python
from ReaderRaman.reader import Single, Multiple
```

### Misura Singola

Lettura di singola misura da un singolo file di tipo json.

```python
singolo = Single("data/2025-09-11_10-10-21,202_CohDTS_50ns_480Kavg_25C.json")
```

Si può fare plot:

```python
singolo.plot().show()
singolo.plot(to_plot='apd_1', title='Prova').show()
```

e con parametro `to_plot` si può scegliere quale dato visualizzare (default 'temperature', altrimenti `apd_1`,`apd_2`,`ratio`).

### Misure multiple in una cartella

Lettura di tutti i file di tipo profilo in una cartella, contenente files di tipo json:

```python
from datetime import datetime
folder = 'data/profiles/'
multiple = Multiple(folder,)
multiple = Multiple(folder, n_measure=10)
multiple = Multiple(folder, n_measure=10, start_measure=5)
multiple.plot()
```

dove il comando di plot è analogo a quello per singola misura.

Inoltre è possibile filtrare per posizione o direttamente plottare andamento nel tempo di una lista di posizioni:

```python
array, real_position_m, index_position = multiple.filter_by_position(1000,to_filter='temperature')
multiple.plot_positions_vs_time(1000,to_plot='temperature').show()
multiple.plot_positions_vs_time([1000,3000],to_plot='apd_1').show()
```

### File hdf5

Si possono esportare in un singolo file h5 tutte le misure lette:

```python
multiple.export_to_h5("misure.h5")
```

E poi possono essere ricaricate con:

```python
from ReaderRaman.reader import MultipleH5

multiple = MultipleH5(filename="misure.h5")
```

e l'oggetto `multiple` potrà essere utilizzato come quello generato dai file `json` in una cartella.

## TODO

- [ ] Permettere di ricalcolare temperatura e ratio fornendo coefficienti differenti.
- [ ] Compensare perdite
