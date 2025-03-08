from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
# Pour une application en production, il est fortement recommandé de hacher les mots de passe,
# par exemple en utilisant : from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'ta_cle_secrete'  # Remplace par une clé secrète sécurisée

# --- Configuration de Flask-Mail ---
# Ici, on utilise Gmail comme exemple. Si tu utilises Gmail, pense à créer un mot de passe d'application.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ton_email@gmail.com'      # Remplace par ton email
app.config['MAIL_PASSWORD'] = 'ton_mot_de_passe_app'       # Remplace par ton mot de passe d'application

mail = Mail(app)

# Serializer pour générer des tokens sécurisés (pour confirmation d'email et réinitialisation)
s = URLSafeTimedSerializer(app.secret_key)

# --- Base de données simplifiée ---
# Pour simplifier, nous utilisons un dictionnaire pour stocker les utilisateurs.
# En production, utilise une vraie base de données et n'oublie pas de hacher les mots de passe.
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
                      sender=app.config['MAIL_USERNAME'],
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
    except Exception as e:
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
    except Exception as e:
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

