from flask import (
    Blueprint, jsonify, request, current_app
)
from . import db
import logging
import datetime
import logging

bp = Blueprint('pwm', __name__, url_prefix='/pwm')

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bp.route('/menu_items', methods=['GET'])
def get_menu_items():
    connection = db.get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, image_path, price FROM menu_items")
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(items)



@bp.route('/abbonamenti', methods=['GET'])
def get_abbonamenti():
    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM abbonamenti")
        abbonamenti = cursor.fetchall()
    except db.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
    return jsonify(abbonamenti), 200

@bp.route('/Users', methods=['GET'])
def get_users():
    connection = db.get_db()
    resp = []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users")

        users = cursor.fetchall()
        for user in users:
            resp.append({
                'user_id': user['user_id'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'email': user['email'],
                'password': user['password'],
                'sesso': user['sesso']
                
            })
    except db.IntegrityError:
        resp.append({'error': 'Error retrieving users'})
    finally:
        cursor.close()
    return jsonify(resp)

@bp.route('/Users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    connection = db.get_db()
    resp = {}
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            resp = {
                'user_id': user['user_id'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'email': user['email'],
                'password': user['password'],
                'sesso': user['sesso'],
                'saldo': user.get('saldo', 0.0),  
                'corse_gratuite': user.get('corse_gratuite', 0)  
            }
        else:
            resp = {'error': 'User not found'}
    except db.IntegrityError:
        resp = {'error': 'Error retrieving user'}
    finally:
        cursor.close()
    return jsonify(resp)
@bp.route('/Users', methods=['POST'])
def create_user():
    nome = request.json.get('nome')
    cognome = request.json.get('cognome')
    email = request.json.get('email')
    password = request.json.get('password')
    sesso = request.json.get('sesso')

    logger.info(f"Received data: nome={nome}, cognome={cognome}, email={email}, password={password}, sesso={sesso}")

    if not nome or not cognome or not email or not password or not sesso:
        return jsonify({"error": "Missing required fields"}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Users (nome, cognome, email, password, sesso, saldo, corse_gratuite) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nome, cognome, email, password, sesso, 0, 0)
        )
        connection.commit()
        user_id = cursor.lastrowid
        resp = {'id': user_id, 'nome': nome, 'cognome': cognome, 'email': email, 'sesso': sesso, 'saldo': 0, 'corse_gratuite': 0}
    except db.IntegrityError as e:
        logger.error(f"Error creating user: {str(e)}")
        resp = {'error': 'Error creating user'}
        return jsonify(resp), 500
    finally:
        cursor.close()
    return jsonify(resp), 201

@bp.route('/Users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    nome = request.json.get('nome')
    cognome = request.json.get('cognome')
    email = request.json.get('email')
    password = request.json.get('password')
    sesso = request.json.get('sesso')

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        if password:
            cursor.execute(
                "UPDATE Users SET nome = %s, cognome = %s, email = %s, password = %s, sesso = %s WHERE user_id = %s",
                (nome, cognome, email, password, sesso, user_id)
            )
        else:
            cursor.execute(
                "UPDATE Users SET nome = %s, cognome = %s, email = %s, sesso = %s WHERE user_id = %s",
                (nome, cognome, email, sesso, user_id)
            )
        connection.commit()
        resp = {'id': user_id, 'nome': nome, 'cognome': cognome, 'email': email, 'sesso': sesso}
    except db.IntegrityError as e:
        logger.error(f"Error updating user: {str(e)}")
        resp = {'error': 'Error updating user'}
        return jsonify(resp), 500
    finally:
        cursor.close()
    return jsonify(resp)
@bp.route('/Users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
        connection.commit()
        resp = {'message': 'User deleted successfully'}
    except db.IntegrityError:
        resp = {'error': 'Error deleting user'}
    finally:
        cursor.close()
    return jsonify(resp)

@bp.route('/login', methods=['POST'])
def login_user():
    email = request.json.get('email')
    password = request.json.get('password')
    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            resp = {
                'user_id': user['user_id'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'email': user['email'],
                'sesso': user['sesso'],
                'saldo': user['saldo'],
                'corse_gratuite': user['corse_gratuite']
            }
        else:
            resp = {'error': 'Invalid email or password'}
            return jsonify(resp), 401
    except db.IntegrityError:
        resp = {'error': 'Error logging in'}
        return jsonify(resp), 500
    finally:
        cursor.close()
    return jsonify(resp), 200

@bp.route('/stations', methods=['GET'])
def get_stations():
    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT station_id, station_name, city FROM Stations")
        stations = [{"stationId": row["station_id"], "stationName": row["station_name"], "city": row["city"]} for row in cursor.fetchall()]
    except db.IntegrityError:
        return jsonify({'error': 'Error retrieving stations'}), 500
    finally:
        cursor.close()
    return jsonify(stations), 200



def timedelta_to_str(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
@bp.route('/tickets', methods=['POST'])
def create_ticket():
    connection = db.get_db()
    data = request.json

    schedule_id = data.get('schedule_id')
    user_id = data.get('user_id')
    seat_number = data.get('seat_number')

    if not schedule_id or not user_id or not seat_number:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Tickets (schedule_id, user_id, seat_number, isValidated) VALUES (%s, %s, %s, %s)",
            (schedule_id, user_id, seat_number, 0)
        )
        connection.commit()
        ticket_id = cursor.lastrowid
        resp = {
            'ticket_id': ticket_id,
            'schedule_id': schedule_id,
            'user_id': user_id,
            'seat_number': seat_number,
            'isValidated': 0
        }
    except db.IntegrityError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    return jsonify(resp), 201


  
@bp.route('/schedules', methods=['GET'])
def get_schedules():
    connection = db.get_db()
    start_station = request.args.get('startStation')
    end_station = request.args.get('endStation')
    date = request.args.get('date')

    logger.info(f"Received parameters: startStation={start_station}, endStation={end_station}, date={date}")

    if not date:
        return jsonify({'error': 'Date parameter is missing'}), 400

    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    query = """
        SELECT s.schedule_id, r.route_id, s.arrival_date, s.departure_date, s.arrival_time, s.departure_time,
               ss.station_name AS start_station, es.station_name AS end_station
        FROM Schedules s
        JOIN Routes r ON s.route_id = r.route_id
        JOIN Stations ss ON r.start_station_id = ss.station_id
        JOIN Stations es ON r.end_station_id = es.station_id
        WHERE ss.station_name = %s AND es.station_name = %s AND s.departure_date = %s
    """
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (start_station, end_station, date))
        schedules = cursor.fetchall()

        for schedule in schedules:
            if isinstance(schedule['arrival_time'], datetime.timedelta):
                schedule['arrival_time'] = timedelta_to_str(schedule['arrival_time'])
            if isinstance(schedule['departure_time'], datetime.timedelta):
                schedule['departure_time'] = timedelta_to_str(schedule['departure_time'])

        logger.info(f"Schedules fetched: {schedules}")
    except db.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    return jsonify(schedules), 200
def log_and_convert_timedelta(data):
    for item in data:
        for key, value in item.items():
            if isinstance(value, datetime.timedelta):
                item[key] = str(value)
            logger.info(f"{key}: {item[key]}")
    return data

@bp.route('/tickets', methods=['GET'])
def get_tickets():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT t.ticket_id, t.seat_number, t.isValidated,
                   ss.station_name AS start_station, es.station_name AS end_station, 
                   s.departure_date, s.arrival_date, s.departure_time, s.arrival_time
            FROM Tickets t
            JOIN Schedules s ON t.schedule_id = s.schedule_id
            JOIN Routes r ON s.route_id = r.route_id
            JOIN Stations ss ON r.start_station_id = ss.station_id
            JOIN Stations es ON r.end_station_id = es.station_id
            WHERE t.user_id = %s
        """
        cursor.execute(query, (user_id,))
        tickets = cursor.fetchall()
        
        # Log and convert timedelta fields
        tickets = log_and_convert_timedelta(tickets)

    except db.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    return jsonify(tickets), 200


@bp.route('/offers', methods=['GET'])
def get_offers():
    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM Offers"
        cursor.execute(query)
        offers = cursor.fetchall()
    except db.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
    return jsonify(offers), 200

@bp.route('/redeem_offer', methods=['POST'])
def redeem_offer():
    user_id = request.json.get('user_id')
    offer_id = request.json.get('offer_id')

    if not user_id or not offer_id:
        return jsonify({'error': 'User ID and Offer ID are required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)

        # Verifica se l'offerta è già stata riscattata dall'utente
        query = "SELECT * FROM riscattate WHERE user_id = %s AND offer_id = %s"
        cursor.execute(query, (user_id, offer_id))
        existing_offer = cursor.fetchone()

        if existing_offer:
            return jsonify({'error': 'Offer already redeemed'}), 400

        # Riscatta l'offerta
        query = "INSERT INTO riscattate (user_id, offer_id) VALUES (%s, %s)"
        cursor.execute(query, (user_id, offer_id))
        connection.commit()
    except db.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Offer redeemed successfully'}), 201

    return jsonify({'message': 'Offer redeemed successfully'}), 201
@bp.route('/update_saldo', methods=['POST'])
def update_saldo():
    user_id = request.json.get('user_id')
    amount = request.json.get('amount')

    if user_id is None or amount is None:
        return jsonify({'error': 'User ID and amount are required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE Users SET saldo = saldo + %s WHERE user_id = %s", (amount, user_id))
        connection.commit()
        cursor.close()
        return jsonify({'message': 'Saldo updated successfully'}), 200
    except db.Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
@bp.route('/img/<path:filename>')
def flask_img(filename):
    return current_app.send_static_file("img/" + filename)


@bp.route('/orders', methods=['POST'])
def create_order():
    user_id = request.json.get('user_id')
    ticket_id = request.json.get('ticket_id')
    total_price = request.json.get('total_price')
    items = request.json.get('items')

    if not user_id or not ticket_id or not total_price or not items:
        return jsonify({'error': 'User ID, ticket ID, total price, and items are required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Orders (user_id, ticket_id, total_price) VALUES (%s, %s, %s)",
            (user_id, ticket_id, total_price)
        )
        order_id = cursor.lastrowid

        for item in items:
            menu_item_id = item['menu_item_id']
            quantity = item['quantity']
            cursor.execute(
                "INSERT INTO OrderItems (order_id, menu_item_id, quantity) VALUES (%s, %s, %s)",
                (order_id, menu_item_id, quantity)
            )

        connection.commit()
        cursor.close()

        return jsonify({'message': 'Order created successfully'}), 201
    except db.Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    
@bp.route('/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    ticket_id = request.args.get('ticket_id')

    if user_id is None or ticket_id is None:
        return jsonify({'error': 'User ID and ticket ID are required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT oi.quantity, mi.name as item_name, mi.price as item_price
            FROM OrderItems oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            JOIN Orders o ON oi.order_id = o.order_id
            WHERE o.user_id = %s AND o.ticket_id = %s
        """, (user_id, ticket_id))
        order_items = cursor.fetchall()
        cursor.close()
        return jsonify(order_items), 200
    except db.Error as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/update_free_rides', methods=['POST'])
def update_free_rides():
    data = request.get_json()
    user_id = data.get('user_id')
    rides_to_use = data.get('rides_to_use')

    if user_id is None or rides_to_use is None:
        return jsonify({"error": "User ID and rides to use are required"}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE Users SET corse_gratuite = corse_gratuite - %s WHERE user_id = %s", (rides_to_use, user_id))
        connection.commit()
        return jsonify({"message": "Free rides updated successfully"}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@bp.route('/riscattate', methods=['GET'])
def get_user_offers():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT o.offer_id, o.description, o.discount_percentage, o.valid_from, o.valid_to, o.price, o.start_station, o.end_station
            FROM riscattate r
            JOIN offers o ON r.offer_id = o.offer_id
            WHERE r.user_id = %s
        """
        cursor.execute(query, (user_id,))
        offers = cursor.fetchall()
        logger.info(f"Fetched offers for user {user_id}: {offers}")
    except db.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    return jsonify(offers), 200

@bp.route('/redeem_offer', methods=['DELETE'])
def delete_redeemed_offer():
    user_id = request.args.get('user_id')
    offer_id = request.args.get('offer_id')

    if not user_id or not offer_id:
        current_app.logger.error('Missing user_id or offer_id')
        return jsonify({'error': 'User ID and Offer ID are required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        query = "DELETE FROM riscattate WHERE user_id = %s AND offer_id = %s"
        cursor.execute(query, (user_id, offer_id))
        connection.commit()
        current_app.logger.info(f'Offer {offer_id} redeemed by user {user_id} successfully removed')
    except db.Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    return jsonify({'message': 'Offer redeemed successfully'}), 200
@bp.route('/delete_ticket', methods=['POST'])
def delete_ticket():
    logger.info("Received delete_ticket request")
    ticket_id = request.json.get('ticket_id')
    logger.info(f"Ticket ID: {ticket_id}")

    if ticket_id is None:
        return jsonify({'error': 'Ticket ID is required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        
        # Elimina i record collegati nelle tabelle orderitems e orders
        cursor.execute("DELETE oi FROM OrderItems oi JOIN Orders o ON oi.order_id = o.order_id WHERE o.ticket_id = %s", (ticket_id,))
        connection.commit()
        
        cursor.execute("DELETE FROM Orders WHERE ticket_id = %s", (ticket_id,))
        connection.commit()
        
        # Ora elimina il ticket
        cursor.execute("DELETE FROM Tickets WHERE ticket_id = %s", (ticket_id,))
        connection.commit()
        
        cursor.close()
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    except mysql.connector.Error as e:
        connection.rollback()
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@bp.route('/tickets/<int:ticket_id>/validate', methods=['PUT'])
def validate_ticket(ticket_id):
    data = request.json
    is_validated = data.get('isValidated')

    if is_validated is None:
        return jsonify({'error': 'Missing isValidated field'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE Tickets SET isValidated = %s WHERE ticket_id = %s", (is_validated, ticket_id))
        connection.commit()
        return jsonify({"message": "Ticket validated successfully"}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()
@bp.route('/check_email', methods=['POST'])
def check_email():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users WHERE email = %s", (email,))
        count = cursor.fetchone()[0]
        cursor.close()
        return jsonify({'exists': count > 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/addcorsegratuite', methods=['POST'])
def add_corse_gratuite():
    data = request.get_json()
    user_id = data.get('user_id')
    corse_gratuite = data.get('corse_gratuite')

    current_app.logger.info(f"Received request to add corse_gratuite: {data}")

    if user_id is None or corse_gratuite is None:
        current_app.logger.error("Missing user_id or corse_gratuite")
        return jsonify({"error": "User ID and corse_gratuite are required"}), 400

    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)  
        current_app.logger.info(f"Updating corse_gratuite for user_id: {user_id} with value: {corse_gratuite}")
        cursor.execute(
            "UPDATE Users SET corse_gratuite = corse_gratuite + %s WHERE user_id = %s",
            (corse_gratuite, user_id)
        )
        connection.commit()

        cursor.execute("SELECT corse_gratuite FROM Users WHERE user_id = %s", (user_id,))
        new_corse_gratuite = cursor.fetchone()
        current_app.logger.info(f"Query result for new corse_gratuite: {new_corse_gratuite}")

        if new_corse_gratuite is None:
            raise ValueError(f"No user found with user_id: {user_id}")

        new_corse_gratuite_value = new_corse_gratuite['corse_gratuite']
        current_app.logger.info(f"New corse_gratuite for user_id {user_id}: {new_corse_gratuite_value}")

        return jsonify({"message": "Corse gratuite aggiunte con successo", "corse_gratuite": new_corse_gratuite_value}), 200
    except Exception as e:
        connection.rollback()
        current_app.logger.error(f"Error updating corse_gratuite for user_id {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()
@bp.route('/notizie', methods=['GET'])
def get_notizie():
    connection = db.get_db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Notizie")
        notizie = cursor.fetchall()
    except db.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
    return jsonify(notizie), 200