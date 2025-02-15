import os
import requests  # type: ignore
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv  # type: ignore
import random  # Per generare numeri casuali

# Carica le variabili dal file .env
load_dotenv()
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

app = Flask(__name__)

# Funzione per la valutazione dell'idea
def evaluate_idea(user_idea):
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    data = {
        "inputs": f"Evaluate this idea in 5 aspects: Creativity, Feasibility, Market Potential, Virality, Time Needed: {user_idea}",
        "parameters": {"max_length": 200}
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct",
            headers=headers,
            json=data
        )
        response.raise_for_status()  # Verifica se ci sono errori HTTP

        # Gestione della risposta se la richiesta è andata a buon fine
        if response.status_code == 200:
            result = response.json()
            generated_text = result[0]["generated_text"]
            print(f"Generated Text: {generated_text}")  # Debug
            return generated_text
        else:
            return f"Error: {response.status_code}, {response.text}"

    except requests.exceptions.RequestException as e:
        return f"Request Error: {str(e)}"

# Funzione per analizzare la valutazione e dividere i punteggi per i vari aspetti
def parse_evaluation(evaluation):
    aspects = {
        "Creativity": 0,
        "Feasibility": 0,
        "Market Potential": 0,
        "Virality": 0,
        "Time Needed": ""  # Aggiunto Time Needed qui
    }

    # Funzione per assegnare un punteggio casuale tra 50 e 100, con logica per "Feasibility"
    def calculate_score(aspect, is_feasibility=False):
        # Se l'aspetto è la fattibilità e l'idea contiene parole "difficili", riduce il punteggio
        if is_feasibility and ("impossible" in evaluation or "difficult" in evaluation):
            return round(random.uniform(10, 40), 2)  # Diminuisce drasticamente la fattibilità
        else:
            return round(random.uniform(50, 100), 2)

    # Calcola il punteggio per ogni aspetto
    aspects["Creativity"] = calculate_score("Creativity")
    aspects["Market Potential"] = calculate_score("Market Potential")
    aspects["Virality"] = calculate_score("Virality")
    aspects["Feasibility"] = calculate_score("Feasibility", is_feasibility=True)

    # Calcola un "tempo necessario" basato sulla difficoltà dell'idea
    if "impossible" in evaluation or "difficult" in evaluation:
        aspects["Time Needed"] = f"{random.randint(5, 10)} years"  # Tra 5 e 10 anni
    elif "complex" in evaluation or "long" in evaluation:
        aspects["Time Needed"] = f"{random.randint(6, 18)} months"  # Tra 6 e 18 mesi
    elif "simple" in evaluation or "quick" in evaluation:
        aspects["Time Needed"] = f"{random.randint(30, 120)} days"  # Tra 30 e 120 giorni
    else:
        aspects["Time Needed"] = f"{random.randint(3, 12)} months"  # Default tra 3 e 12 mesi

    # Debug: mostra i punteggi calcolati per ciascun aspetto
    print(f"Aspects: {aspects}")

    # Calcola la media finale dei punteggi (senza considerare il "Time Needed")
    final_score = (aspects["Creativity"] + aspects["Feasibility"] + aspects["Market Potential"] + aspects["Virality"]) / 4

    # Aggiungi un incremento minimo per garantire che il punteggio non sia troppo basso
    if final_score < 60:
        final_score += 5  # Aumenta il punteggio di 5 punti se troppo basso

    # Limita il punteggio finale a 90 (per evitare che diventi troppo alto)
    final_score = min(final_score, 90)

    return aspects, final_score

# Rotta per la homepage
@app.route('/')
def home():
    return render_template('index.html')

# Rotta per valutare l'idea
@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    user_idea = data.get("idea", "")
    
    if not user_idea:
        return jsonify({"error": "No idea provided"}), 400
    
    # Valutazione dell'idea tramite l'API di Hugging Face
    evaluation = evaluate_idea(user_idea)
    
    # Analizza la valutazione e restituisce un punteggio dettagliato
    aspects, final_score = parse_evaluation(evaluation)
    
    # Restituisce i risultati
    return jsonify({
        "evaluation": evaluation,
        "detailed_evaluation": aspects,
        "final_score": final_score
    })

# Rotta per la sezione "Docs"
@app.route('/docs')
def docs():
    return render_template('docs.html')

# Avvia il server
if __name__ == '__main__':
    app.run(debug=True)
