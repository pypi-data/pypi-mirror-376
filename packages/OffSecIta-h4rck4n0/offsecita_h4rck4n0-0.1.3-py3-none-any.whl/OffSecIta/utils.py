from .corsi import corso # importiamo dalla directory corrente il modulo corsi (.corsi) la lista "corso"

# avendo importatato la lista con tutti i corsi possiamo sommare tutte le durate dei corsi

def durata_totale_corsi():

    return sum(corso_sum.durata for corso_sum in corso)
