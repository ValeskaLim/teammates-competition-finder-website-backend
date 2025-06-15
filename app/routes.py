# app/routes.py
from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import User, Competition, UserCompetition, TeamInvitation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from datetime import datetime, date

main = Blueprint('main', __name__)

@main.route('/api/users', methods=['POST'])
def get_users():
    try:
        data = request.get_json();
        query = User.query
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in query.all()],
            "statusCode": 200
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching users: {str(e)}'
        }), 500

@main.route('/api/users/create', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        new_user = User(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            fullname=data['fullname'],
            gender=data['gender'],
            semester=data['semester'],
            major=data['major'],
            field_of_preference=data['field_of_preference']
        )
        
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

# 2. SELECT - Get users by criteria (using POST for complex queries)
@main.route('/api/users/search', methods=['POST'])
def search_users():
    try:
        data = request.get_json()
        query = User.query
        
        # Build dynamic query based on provided criteria
        if 'major' in data and data['major']:
            query = query.filter(User.major.ilike(f"%{data['major']}%"))
        
        if 'semester' in data and data['semester']:
            query = query.filter(User.semester == data['semester'])
        
        if 'gender' in data and data['gender']:
            query = query.filter(User.gender == data['gender'])
        
        if 'field_of_preference' in data and data['field_of_preference']:
            query = query.filter(User.field_of_preference.ilike(f"%{data['field_of_preference']}%"))
        
        # Pagination
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

# =============================================================================
# COMPETITION ROUTES - POST METHODS
# =============================================================================

# 3. INSERT - Create new competition
@main.route('/api/competitions/create', methods=['POST'])
def create_competition():
    try:
        data = request.get_json()
        
        # Parse date string to datetime object
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

# 4. SELECT - Get competitions by filters
@main.route('/api/competitions/filter', methods=['POST'])
def filter_competitions():
    try:
        data = request.get_json()
        query = Competition.query
        
        # Filter by status
        if 'status' in data and data['status']:
            query = query.filter(Competition.status == data['status'])
        
        # Filter by type
        if 'type' in data and data['type']:
            query = query.filter(Competition.type.ilike(f"%{data['type']}%"))
        
        # Filter by date range
        if 'start_date' in data and data['start_date']:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', ''))
            query = query.filter(Competition.date >= start_date)
        
        if 'end_date' in data and data['end_date']:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', ''))
            query = query.filter(Competition.date <= end_date)
        
        # Filter by available slots
        if 'available_slots_only' in data and data['available_slots_only']:
            query = query.filter(Competition.slot > 0)
        
        # Order by date
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

# =============================================================================
# USER COMPETITION ROUTES - POST METHODS
# =============================================================================

# 5. INSERT - Register user for competition
@main.route('/api/user-competitions/register', methods=['POST'])
def register_user_competition():
    try:
        data = request.get_json()
        
        # Check if user already registered for this competition
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
        
        # Check if competition has available slots
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
        
        # Create new registration
        now = datetime.now()
        new_registration = UserCompetition(
            user_id=data['user_id'],
            competition_id=data['competition_id'],
            created_by=data.get('created_by', 'system'),
            date_created=now,
            date_updated=now
        )
        
        # Decrease competition slot
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

# 6. DELETE - Remove user from competition
@main.route('/api/user-competitions/unregister', methods=['POST'])
def unregister_user_competition():
    try:
        data = request.get_json()
        
        # Find the registration
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
        
        # Get competition to increase slot back
        competition = Competition.query.get(data['competition_id'])
        if competition:
            competition.slot += 1
        
        # Store registration info before deletion
        registration_info = registration.to_dict()
        
        # Delete the registration
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