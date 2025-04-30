from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permite requisições de origens diferentes (cross-origin)

# Configuração do banco de dados
DATABASE = 'feedback_data.db'

def init_db():
    """Inicializa o banco de dados se ele não existir"""
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Cria a tabela de feedback
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            room_number TEXT,
            check_in_date TEXT,
            check_out_date TEXT,
            rating_reception INTEGER,
            rating_cleanliness INTEGER,
            rating_comfort INTEGER,
            rating_breakfast INTEGER,
            rating_restaurant INTEGER,
            rating_leisure INTEGER,
            rating_overall INTEGER,
            liked_most TEXT,
            improvements TEXT,
            services TEXT,
            additional_comments TEXT,
            recommend TEXT,
            submitted_date TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print("Banco de dados inicializado com sucesso.")

# Inicializa o banco de dados ao iniciar o aplicativo
init_db()

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Endpoint para receber e processar os dados de feedback"""
    try:
        # Recebe os dados do formulário
        data = request.json
        
        # Extrair os valores do JSON recebido
        name = data.get('name')
        email = data.get('email')
        room_number = data.get('roomNumber')
        check_in_date = data.get('checkInDate')
        check_out_date = data.get('checkOutDate')
        
        ratings = data.get('ratings', {})
        rating_reception = ratings.get('reception', 0)
        rating_cleanliness = ratings.get('cleanliness', 0)
        rating_comfort = ratings.get('comfort', 0)
        rating_breakfast = ratings.get('breakfast', 0)
        rating_restaurant = ratings.get('restaurant', 0)
        rating_leisure = ratings.get('leisure', 0)
        rating_overall = ratings.get('overall', 0)
        
        liked_most = data.get('likedMost')
        improvements = data.get('improvements')
        services = json.dumps(data.get('services', []))  # Converte a lista para JSON
        additional_comments = data.get('additionalComments')
        recommend = data.get('recommend')
        
        submitted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Validações básicas
        if not name or not email:
            return jsonify({'success': False, 'message': 'Nome e e-mail são obrigatórios'}), 400
        
        # Salva os dados no banco de dados
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO feedback (
            name, email, room_number, check_in_date, check_out_date,
            rating_reception, rating_cleanliness, rating_comfort,
            rating_breakfast, rating_restaurant, rating_leisure,
            rating_overall, liked_most, improvements, services,
            additional_comments, recommend, submitted_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, email, room_number, check_in_date, check_out_date,
            rating_reception, rating_cleanliness, rating_comfort,
            rating_breakfast, rating_restaurant, rating_leisure,
            rating_overall, liked_most, improvements, services,
            additional_comments, recommend, submitted_date
        ))
        
        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()
        
        # Envia notificação por e-mail para o hotel
        send_email_notification(data)
        
        return jsonify({
            'success': True,
            'message': 'Feedback recebido com sucesso!',
            'feedback_id': feedback_id
        })
        
    except Exception as e:
        print(f'Erro ao processar feedback: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao processar o feedback: {str(e)}'
        }), 500

def send_email_notification(feedback_data):
    """Envia uma notificação por e-mail para o gerente do hotel"""
    try:
        # Configurações de e-mail (substitua com suas configurações reais)
        email_host = 'smtp.gmail.com'
        email_port = 587
        email_user = 'recepcaolucassouza@gmail.com'
        email_password = 'lpsv dzan pokm wqqa '
        recipient_email = 'lucaszaous@gmail.com'
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = recipient_email
        msg['Subject'] = f'Novo Feedback de Hóspede - {feedback_data["name"]}'
        
        # Formatar o corpo do e-mail
        ratings = feedback_data.get('ratings', {})
        body = f"""
        <html>
        <body>
            <h2>Novo Feedback de Hóspede Recebido</h2>
            <p><strong>Nome:</strong> {feedback_data.get('name')}</p>
            <p><strong>E-mail:</strong> {feedback_data.get('email')}</p>
            <p><strong>Quarto:</strong> {feedback_data.get('roomNumber')}</p>
            <p><strong>Check-in:</strong> {feedback_data.get('checkInDate')}</p>
            <p><strong>Check-out:</strong> {feedback_data.get('checkOutDate')}</p>
            
            <h3>Avaliações</h3>
            <ul>
                <li><strong>Recepção:</strong> {ratings.get('reception', 0)}/5</li>
                <li><strong>Limpeza:</strong> {ratings.get('cleanliness', 0)}/5</li>
                <li><strong>Conforto:</strong> {ratings.get('comfort', 0)}/5</li>
                <li><strong>Café da Manhã:</strong> {ratings.get('breakfast', 0)}/5</li>
                <li><strong>Restaurante:</strong> {ratings.get('restaurant', 0)}/5</li>
                <li><strong>Área de Lazer:</strong> {ratings.get('leisure', 0)}/5</li>
                <li><strong>Avaliação Geral:</strong> {ratings.get('overall', 0)}/5</li>
            </ul>
            
            <h3>Comentários</h3>
            <p><strong>O que mais gostou:</strong><br> {feedback_data.get('likedMost')}</p>
            <p><strong>O que poderia melhorar:</strong><br> {feedback_data.get('improvements')}</p>
            <p><strong>Comentários adicionais:</strong><br> {feedback_data.get('additionalComments')}</p>
            
            <p><strong>Serviços utilizados:</strong> {', '.join(feedback_data.get('services', []))}</p>
            <p><strong>Recomendaria o hotel:</strong> {feedback_data.get('recommend')}</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Conectar ao servidor e enviar e-mail
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"E-mail de notificação enviado para {recipient_email}")
        
    except Exception as e:
        print(f"Erro ao enviar e-mail de notificação: {str(e)}")
        # Não interromper o fluxo principal se o e-mail falhar

@app.route('/api/feedbacks', methods=['GET'])
def get_feedbacks():
    """Endpoint para obter todos os feedbacks (protegido por autenticação em produção)"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row  # Para obter resultados como dicionários
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback ORDER BY submitted_date DESC')
        feedbacks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Processar os serviços (converter de JSON para lista)
        for feedback in feedbacks:
            if feedback['services']:
                feedback['services'] = json.loads(feedback['services'])
        
        return jsonify({
            'success': True,
            'feedbacks': feedbacks
        })
        
    except Exception as e:
        print(f'Erro ao buscar feedbacks: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar feedbacks: {str(e)}'
        }), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Endpoint para obter dados agregados para o dashboard"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Total de feedbacks
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total_feedbacks = cursor.fetchone()[0]
        
        # Avaliação média por categoria
        cursor.execute('''
        SELECT 
            AVG(rating_reception) as avg_reception,
            AVG(rating_cleanliness) as avg_cleanliness,
            AVG(rating_comfort) as avg_comfort,
            AVG(rating_breakfast) as avg_breakfast,
            AVG(rating_restaurant) as avg_restaurant,
            AVG(rating_leisure) as avg_leisure,
            AVG(rating_overall) as avg_overall
        FROM feedback
        ''')
        averages = cursor.fetchone()
        
        # Percentual de recomendação
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE recommend = 'yes'")
        recommend_yes = cursor.fetchone()[0]
        recommend_percent = (recommend_yes / total_feedbacks * 100) if total_feedbacks > 0 else 0
        
        # Feedbacks recentes (10 últimos)
        cursor.execute('''
        SELECT id, name, rating_overall, submitted_date, recommend
        FROM feedback 
        ORDER BY submitted_date DESC LIMIT 10
        ''')
        recent_feedbacks = [dict(zip(['id', 'name', 'rating', 'date', 'recommend'], row)) for row in cursor.fetchall()]
        
        # Serviços mais utilizados
        cursor.execute('SELECT services FROM feedback')
        all_services = cursor.fetchall()
        
        service_counts = {}
        for services_json in all_services:
            if services_json[0]:
                services = json.loads(services_json[0])
                for service in services:
                    service_counts[service] = service_counts.get(service, 0) + 1
        
        # Converter para lista de dicionários para API
        services_data = [{'service': k, 'count': v} for k, v in service_counts.items()]
        
        conn.close()
        
        # Preparar dados para o dashboard
        dashboard_data = {
            'total_feedbacks': total_feedbacks,
            'averages': {
                'reception': round(averages[0] or 0, 1),
                'cleanliness': round(averages[1] or 0, 1),
                'comfort': round(averages[2] or 0, 1),
                'breakfast': round(averages[3] or 0, 1),
                'restaurant': round(averages[4] or 0, 1),
                'leisure': round(averages[5] or 0, 1),
                'overall': round(averages[6] or 0, 1)
            },
            'recommend_percent': round(recommend_percent, 1),
            'recent_feedbacks': recent_feedbacks,
            'services_data': services_data
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        print(f'Erro ao buscar dados do dashboard: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar dados do dashboard: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Em produção, use um servidor web como Gunicorn
    app.run(debug=True, port=5000)
