from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)

# Remplace 'YOUR_SECRET_KEY' par une clé générée, par exemple avec secrets.token_hex(16)
app.secret_key = '1234567891011'

# --- Configuration de Flask-Mail pour Mailjet ---
# Pour SSL sur le port 465
app.config['MAIL_SERVER'] = 'in-v3.mailjet.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Clé API (API Key) Mailjet
app.config['MAIL_USERNAME'] = '60d3ee0cea1ab10cb22aa027cf08694b'
# Clé API secrète (Secret Key) Mailjet
app.config['MAIL_PASSWORD'] = '28a17b370194526bec3e500f69470a1'

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# --- Base de données simplifiée ---
# Ici, nous utilisons un dictionnaire pour stocker les utilisateurs.
# En production, utilise une base de données et n'oublie pas de hacher les mots de passe.
users = {}  # Format : { email: {'username': '...', 'password': '...'} }

# --- Routes de l'application ---

# Accueil : si l'utilisateur est connecté, il voit un message de bienvenue
@app.route('/')
def index():
    if 'user' in session:
        return f"Bonjour, {session['user']} ! <br><a href='/logout'>Déconnexion</a>"
    return redirect(url_for('login'))

# Inscription : l'utilisateur entre son email pour s'inscrire
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if email in users:
            flash("Cet email est déjà enregistré. Veuillez vous connecter.")
            return redirect(url_for('login'))
        # Génération d'un token de confirmation
        token = s.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirmez votre adresse email',
                      sender=app.config['MAIL_USERNAME'],  # Expéditeur
                      recipients=[email])
        msg.body = (f'Pour terminer votre inscription, cliquez sur ce lien : {confirm_url}\n'
                    f'Ce lien expirera dans 1 heure.')
        mail.send(msg)
        flash('Un email de confirmation a été envoyé. Veuillez vérifier votre boîte mail.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Confirmation de l'inscription : l'utilisateur clique sur le lien reçu par email
@app.route('/confirm/<token>', methods=['GET', 'POST'])
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        return '<h1>Le lien de confirmation est invalide ou a expiré.</h1>'
    
    if request.method == 'POST':
        password = request.form['password']
        username = email.split('@')[0]  # Exemple : le nom d'utilisateur est la partie avant le @
        # En production, n'oublie pas de hacher le mot de passe
        users[email] = {'username': username, 'password': password}
        flash('Votre inscription est confirmée. Vous pouvez maintenant vous connecter.')
        return redirect(url_for('login'))
    return render_template('confirm.html', email=email)

# Connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)
        if user and user['password'] == password:
            session['user'] = user['username']
            flash('Connexion réussie.')
            return redirect(url_for('index'))
        flash('Email ou mot de passe incorrect.')
    return render_template('login.html')

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Vous avez été déconnecté.')
    return redirect(url_for('login'))

# Demande de réinitialisation du mot de passe
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        if email not in users:
            flash("Cet email n'est pas enregistré.")
            return redirect(url_for('reset_password'))
        token = s.dumps(email, salt='password-reset')
        reset_url = url_for('reset_with_token', token=token, _external=True)
        msg = Message('Réinitialisation de votre mot de passe',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = (f'Pour réinitialiser votre mot de passe, cliquez sur ce lien : {reset_url}\n'
                    f'Ce lien expirera dans 1 heure.')
        mail.send(msg)
        flash('Un email de réinitialisation du mot de passe a été envoyé.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

# Réinitialisation du mot de passe via le token
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        return '<h1>Le lien de réinitialisation est invalide ou a expiré.</h1>'
    
    if request.method == 'POST':
        new_password = request.form['password']
        if email in users:
            users[email]['password'] = new_password  # N'oublie pas de hacher le mot de passe en production
            flash('Votre mot de passe a été réinitialisé. Vous pouvez vous connecter.')
            return redirect(url_for('login'))
        else:
            flash("Email non trouvé.")
            return redirect(url_for('reset_password'))
    return render_template('reset_with_token.html', email=email)

if __name__ == '__main__':
    app.run(debug=True)


