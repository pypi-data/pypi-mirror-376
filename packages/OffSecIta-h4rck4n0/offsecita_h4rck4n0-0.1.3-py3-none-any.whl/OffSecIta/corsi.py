
# Creiamo una classe di oggetti Corsi
class Corsi:

    def __init__(self, nome, durata, link):

        self.nome = nome
        self.durata = durata
        self.link = link

    def __repr__(self):   # usiamo il metodo speciale per vesualizzare il contenuto dei oggetti
        return f"\n[+] Nome Corso: {self.nome}, Durata: [{self.durata}], link: {self.link}"

# creiamo una lista di oggetti Corsi 
corso = [
    Corsi("Corso Hacking Etico", 60, "https://www.youtube.com/playlist?list=PLKZZXjqZrqQtKGgJuAYhzYczf1KIdswvO"),
    Corsi("Corso Linux", 15, "https://www.youtube.com/watch?v=UaFto4RvUCk&list=PLKZZXjqZrqQtSRw3fFdA9JSnTrmCrhw8p"),
    Corsi("Corso Python", 50, "https://www.youtube.com/playlist?list=PLKZZXjqZrqQu7qZkgSsdU3lRpR7oISMXh"),
    Corsi("Corso Personalizzazione Linux", 3, "https://www.youtube.com/playlist?list=PLKZZXjqZrqQslOV4EyEl40ZPxo7bpFHQE")
        ]


def lista_corsi():
    # iteriamo e stampiamo la lista corso
    for info_corso in corso:
        print(info_corso) 

def cerca_corso_nome(nome):
    for trova in corso:
        if trova.nome == nome:
            return trova    
    return None

