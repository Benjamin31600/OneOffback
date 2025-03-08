from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import io, csv

app = Flask(__name__)
app.secret_key = "ta_cle_secrete"  # Clé pour sécuriser les sessions

# "Base de données" simplifiée pour les utilisateurs
users = {
    "user@example.com": {"password": "1234", "username": "Utilisateur"}
}

@app.route("/")
def index():
    if "user" in session:
        return render_template("dashboard.html", username=session["user"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and users[email]["password"] == password:
            session["user"] = users[email]["username"]
            return redirect(url_for("index"))
        else:
            message = "Email ou mot de passe incorrect"
    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

def calculer_cout_global(prix_achat, taux_depreciation, quantite):
    cout_depreciation = prix_achat * taux_depreciation
    cout_global = (prix_achat + cout_depreciation) * quantite
    return cout_global

@app.route("/calcul", methods=["POST"])
def calcul():
    prix_achat = float(request.form["prix_achat"])
    taux_depreciation = float(request.form["taux_depreciation"])
    quantite = int(request.form["quantite"])
    
    cout = calculer_cout_global(prix_achat, taux_depreciation, quantite)
    return render_template("resultat.html", cout=cout)

def verifier_stock(quantite, seuil):
    if quantite < seuil:
        return "Attention : il est temps de recommander !"
    else:
        return "Stock suffisant."

@app.route("/alerte_stock", methods=["POST"])
def alerte_stock():
    quantite = int(request.form["quantite"])
    seuil = int(request.form["seuil"])
    message_alerte = verifier_stock(quantite, seuil)
    return render_template("alerte.html", message=message_alerte)

@app.route("/export_csv")
def export_csv():
    data = [
        ["Produit", "Quantité", "Coût"],
        ["Produit A", 10, 15.0],
        ["Produit B", 5, 20.0]
    ]
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(data)
    output = si.getvalue()
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="export.csv"'
    }

# Optionnel : API pour récupérer le coût en JSON
@app.route("/api/cout", methods=["POST"])
def api_cout():
    data = request.get_json()
    prix_achat = float(data["prix_achat"])
    taux_depreciation = float(data["taux_depreciation"])
    quantite = int(data["quantite"])
    cout = calculer_cout_global(prix_achat, taux_depreciation, quantite)
    return jsonify({"cout_global": cout})

if __name__ == "__main__":
    app.run(debug=True)

