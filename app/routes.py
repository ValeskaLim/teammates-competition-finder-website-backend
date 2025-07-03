from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Users, Competition, UserCompetition, TeamInvitation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from datetime import datetime, date
from flask_cors import CORS


main = Blueprint('main', __name__)

@main.route('/api/user/get-all-user', methods=['POST'])
def get_users():
    try:
        query = Users.query

        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in query.all()],
            "statusCode": 200
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching users: {str(e)}'
        }), 500
        
@main.route('/api/auth/validate-user', methods=['POST'])
def validate_user():
    try:
        req = request.get_json()
        
        is_user_exist = Users.query.filter(
            (Users.email == req['email']) & (Users.password == req['password'])).first()
        
        print(req)
        
        if is_user_exist is None:
            return jsonify({
            'success': False,
            'message': f'Invalid email or password'
        }), 500
            
        return jsonify({
            'success': True,
            'message': f'Login successful',
            'user': is_user_exist.to_dict()
        }), 200
            
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error validating user'
        }), 500
        
@main.route('/api/user/get-existing-user', methods=['POST'])
def get_existing_user():
    try:
        req = request.get_json()
        
        query = Users.query
        
        existing_username = query.filter(
            (Users.username == req['username'])
        ).first()
        
        existing_email = query.filter(
            Users.email == req['email']
        ).first()
        
        return jsonify({
            'success': True,
            'usernameExist': existing_username is not None,
            'emailExist': existing_email is not None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting user: {str(e)}'
        }), 500

@main.route('/api/user/submit-register-data', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # List of required fields
        required_fields = ['username', 'password', 'email', 'fullname', 'gender', 'semester', 'field_of_preference']
        
        # Validate empty fields
        for field in required_fields:
            if field not in data or data[field] == "":
                return jsonify({
                    'success': False,
                    'message': f'Missing or empty required field: {field[0].upper() + field[1:]}'
                }), 400

        if ' ' in data['username']:
            return jsonify({
                'success': False,
                'message': 'Username cannot contain spaces'
            }), 400
                
        # Validate email format and password length
        if data['email'].find('@') == -1:
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        if len(data['password']) < 4:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 4 characters long'
            }), 400

        # Check for existing username or email
        existing_user = Users.query.filter(
        (Users.username == data['username']) | (Users.email == data['email'])).first()

        print("Is existing", existing_user)
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username or email already exists'
            }), 400
                
        new_user = Users(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            fullname=data['fullname'],
            gender=data['gender'],
            semester=data['semester'],
            major= 'Computer Science',
            field_of_preference=data['field_of_preference']
        )
        
        print("Data received:", new_user.to_dict())
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': new_user.user_id,
            'user': new_user.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Username or email already exists'
        }), 400
    except KeyError as e:
        return jsonify({
            'success': False,
            'message': f'Missing required field: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating user: {str(e)}'
        }), 500

@main.route('/api/user/search', methods=['POST'])
def search_users():
    try:
        data = request.get_json()
        query = Users.query
        
        if 'major' in data and data['major']:
            query = query.filter(Users.major.ilike(f"%{data['major']}%"))
        
        if 'semester' in data and data['semester']:
            query = query.filter(Users.semester == data['semester'])
        
        if 'gender' in data and data['gender']:
            query = query.filter(Users.gender == data['gender'])
        
        if 'field_of_preference' in data and data['field_of_preference']:
            query = query.filter(Users.field_of_preference.ilike(f"%{data['field_of_preference']}%"))
        
        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        
        users = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': users.page
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error searching users: {str(e)}'
        }), 500

@main.route('/api/competitions/create', methods=['POST'])
def create_competition():
    try:
        data = request.get_json()
        
        competition_date = datetime.fromisoformat(data['date'].replace('Z', ''))
        
        new_competition = Competition(
            title=data['title'],
            date=competition_date,
            status=data['status'],
            description=data['description'],
            type=data['type'],
            slot=data['slot']
        )
        
        db.session.add(new_competition)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Competition created successfully',
            'competition_id': new_competition.competition_id,
            'competition': new_competition.to_string()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Competition title already exists'
        }), 400
    except KeyError as e:
        return jsonify({
            'success': False,
            'message': f'Missing required field: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating competition: {str(e)}'
        }), 500

@main.route('/api/competitions/filter', methods=['POST'])
def filter_competitions():
    try:
        data = request.get_json()
        query = Competition.query
        
        if 'status' in data and data['status']:
            query = query.filter(Competition.status == data['status'])
        
        if 'type' in data and data['type']:
            query = query.filter(Competition.type.ilike(f"%{data['type']}%"))
        
        if 'start_date' in data and data['start_date']:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', ''))
            query = query.filter(Competition.date >= start_date)
        
        if 'end_date' in data and data['end_date']:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', ''))
            query = query.filter(Competition.date <= end_date)
        
        if 'available_slots_only' in data and data['available_slots_only']:
            query = query.filter(Competition.slot > 0)
        
        order_by = data.get('order_by', 'date')
        order_direction = data.get('order_direction', 'asc')
        
        if order_direction.lower() == 'desc':
            query = query.order_by(getattr(Competition, order_by).desc())
        else:
            query = query.order_by(getattr(Competition, order_by))
        
        competitions = query.all()
        
        return jsonify({
            'success': True,
            'competitions': [comp.to_string() for comp in competitions],
            'count': len(competitions)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error filtering competitions: {str(e)}'
        }), 500

@main.route('/api/user-competitions/register', methods=['POST'])
def register_user_competition():
    try:
        data = request.get_json()
        
        existing_registration = UserCompetition.query.filter(
            and_(
                UserCompetition.user_id == data['user_id'],
                UserCompetition.competition_id == data['competition_id']
            )
        ).first()
        
        if existing_registration:
            return jsonify({
                'success': False,
                'message': 'User already registered for this competition'
            }), 400
        
        competition = Competition.query.get(data['competition_id'])
        if not competition:
            return jsonify({
                'success': False,
                'message': 'Competition not found'
            }), 404
        
        if competition.slot <= 0:
            return jsonify({
                'success': False,
                'message': 'No available slots for this competition'
            }), 400
        
        now = datetime.now()
        new_registration = UserCompetition(
            user_id=data['user_id'],
            competition_id=data['competition_id'],
            created_by=data.get('created_by', 'system'),
            date_created=now,
            date_updated=now
        )
        
        competition.slot -= 1
        
        db.session.add(new_registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered for competition successfully',
            'registration': new_registration.to_dict()
        }), 201
        
    except KeyError as e:
        return jsonify({
            'success': False,
            'message': f'Missing required field: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error registering user: {str(e)}'
        }), 500

@main.route('/api/user-competitions/unregister', methods=['POST'])
def unregister_user_competition():
    try:
        data = request.get_json()
        
        registration = UserCompetition.query.filter(
            and_(
                UserCompetition.user_id == data['user_id'],
                UserCompetition.competition_id == data['competition_id']
            )
        ).first()
        
        if not registration:
            return jsonify({
                'success': False,
                'message': 'Registration not found'
            }), 404
        
        competition = Competition.query.get(data['competition_id'])
        if competition:
            competition.slot += 1
        
        registration_info = registration.to_dict()
        
        db.session.delete(registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User unregistered from competition successfully',
            'deleted_registration': registration_info
        }), 200
        
    except KeyError as e:
        return jsonify({
            'success': False,
            'message': f'Missing required field: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error unregistering user: {str(e)}'
        }), 500