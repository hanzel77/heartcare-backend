from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pickle
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('MYSQLUSER')}:{os.getenv('MYSQLPASSWORD')}@{os.getenv('MYSQLHOST')}:{os.getenv('MYSQLPORT')}/{os.getenv('MYSQL_DATABASE')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    return jsonify({"message": "HeartCare Backend is running!"}), 200

@app.route('/test-db', methods=['GET'])
def test_db_connection():
    try:
        # Attempt to connect to the database by querying a simple table check
        result = db.session.execute('SELECT 1')
        return jsonify({"message": "Database connection successful!"}), 200
    except Exception as e:
        return jsonify({"error": f"Database connection failed: {str(e)}"}), 500


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    sex = db.Column(db.String(10), nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    smoking_history = db.Column(db.Boolean, nullable=True)
    skin_cancer = db.Column(db.Boolean, nullable=True)
    other_cancer = db.Column(db.Boolean, nullable=True)
    diabetes = db.Column(db.Boolean, nullable=True)
    arthritis = db.Column(db.Boolean, nullable=True)
    depression = db.Column(db.Boolean, nullable=True)

    emergency_contacts = db.relationship(
        'EmergencyContacts',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    reports = db.relationship(
        'Reports',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

class EmergencyContacts(db.Model):
    __tablename__ = 'emergency_contacts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    user_id = db.Column(db.String(50), db.ForeignKey('user.user_id'), nullable=False) 
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)

class Reports(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.user_id'), nullable=False)
    report_date = db.Column(db.DateTime, nullable=False)
    report_probability = db.Column(db.Float, nullable=False)
    report_prediction = db.Column(db.Integer, nullable=False)
    

@app.route("/api/register", methods=["POST"])
def create_user():
    try:
        data = request.json  
        
        if not data.get('email') or not data.get('uid') or not data.get('password') or not data.get('name'):
            return jsonify({"error": "Email, password, and name are required."}), 400
        
        new_user = User(
            user_id=data['uid'],
            name=data['name'],
            email=data['email'],
            password=data['password'], 
        )
        
        # Add user to the database
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/<string:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        return jsonify({
            'user_id': user.user_id,
            'name': user.name,
            'email': user.email,
            'password': user.password,
            'age': user.age,
            'sex': user.sex,
            'height_cm': user.height_cm,
            'weight_kg': user.weight_kg,
            'smoking_history': user.smoking_history,
            'skin_cancer': user.skin_cancer,
            'other_cancer': user.other_cancer,
            'diabetes': user.diabetes,
            'arthritis': user.arthritis,
            'depression': user.depression    
        }, 200)
    
@app.route("/api/user/<string:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        data = request.json
        user.age = data.get("age", user.age)
        user.sex = data.get("sex", user.sex)
        user.height_cm = data.get("height_cm", user.height_cm)
        user.weight_kg = data.get("weight_kg", user.weight_kg)
        user.smoking_history = data.get("smoking_history", user.smoking_history)
        user.skin_cancer = data.get("skin_cancer", user.skin_cancer)
        user.other_cancer = data.get("other_cancer", user.other_cancer)
        user.diabetes = data.get("diabetes", user.diabetes)
        user.arthritis = data.get("arthritis", user.arthritis)
        user.depression = data.get("depression", user.depression)

        db.session.commit()
        return jsonify({"message": "User profile updated successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Prediction
@app.route("/api/predict/<string:user_id>", methods=["POST"])
def predict(user_id):
    try:
        model_path = "model_xgboost.pkl"
        with open(model_path, "rb") as file:
            model = pickle.load(file)
            print("Model loaded successfully!")

        data = request.json
        required_fields = [
            "General_Health",
            "Checkup",
            "Exercise",
            "Skin_Cancer",
            "Other_Cancer",
            "Depression",
            "Diabetes",
            "Arthritis",
            "Sex",
            "Age",
            "Height_(cm)",
            "Weight_(kg)",
            "Smoking_History",
            "Alcohol_Consumption",
            "Fruit_Consumption",
            "Green_Vegetables_Consumption",
            "FriedPotato_Consumption"
        ]

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
        

        # Replace categorical values with numerical values directly in the data dictionary
        data['General_Health'] = {
            'excellent': 4,
            'very_good': 3,
            'good': 2,
            'fair': 1,
            'poor': 0
        }.get(data['General_Health'], data['General_Health'])

        data['Checkup'] = {
            'within_1_year': 4,
            'within_2_years': 3,
            'within_5_years': 2,
            '5_or_more_years': 1,
            'never': 0,
        }.get(data['Checkup'], data['Checkup'])

        # Replace 'Yes'/'No' with 1/0
        for key in ['Exercise', 'Skin_Cancer', 'Other_Cancer', 'Depression', 'Diabetes', 'Arthritis', 'Smoking_History', 'Alcohol_Consumption', 'Fruit_Consumption', 'Green_Vegetables_Consumption', 'FriedPotato_Consumption']:
            data[key] = 1 if data[key] == 'Yes' else 0

        # Assign age category as a string and convert to numerical value
        def assign_age_category(age):
            if 18 <= age <= 24:
                return 0
            elif 25 <= age <= 29:
                return 1
            elif 30 <= age <= 34:
                return 2
            elif 35 <= age <= 39:
                return 3
            elif 40 <= age <= 44:
                return 4
            elif 45 <= age <= 49:
                return 5
            elif 50 <= age <= 54:
                return 6
            elif 55 <= age <= 59:
                return 7
            elif 60 <= age <= 64:
                return 8
            elif 65 <= age <= 69:
                return 9
            elif 70 <= age <= 74:
                return 10
            elif 75 <= age <= 79:
                return 11
            else:
                return 12

        data['Age_Category'] = assign_age_category(data['Age'])

        # Create one-hot encoding for 'Sex'
        data['Sex_Female'] = 1 if data['Sex'] == 'Female' else 0
        data['Sex_Male'] = 1 if data['Sex'] == 'Male' else 0

        height = data["Height_(cm)"] / 100
        weight = data["Weight_(kg)"]
        bmi = weight / (height ** 2)
        data["BMI"] = round(bmi, 2)

        # Prepare the feature list in the order expected by the model
        features = [
            "General_Health",
            "Checkup",
            "Exercise",
            "Skin_Cancer",
            "Other_Cancer",
            "Depression",
            "Diabetes",
            "Arthritis",
            "Age_Category",
            "Height_(cm)",
            "Weight_(kg)",
            "BMI",
            "Smoking_History",
            "Alcohol_Consumption",
            "Fruit_Consumption",
            "Green_Vegetables_Consumption",
            "FriedPotato_Consumption",
            "Sex_Female",
            "Sex_Male"
        ]

        input_features = [data[feature] for feature in features]

        
        prediction = model.predict([input_features])[0]
        prediction_proba = model.predict_proba([input_features])[0]

        response = {
            "Prediction": int(prediction),
            "Prediction Probability": prediction_proba.tolist()
        }
        print(response)

        new_report = Reports(
            user_id=user_id,
            report_date=datetime.now(),
            report_probability=prediction_proba.tolist()[1] ,
            report_prediction=int(prediction)
        )

        db.session.add(new_report)
        db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


# Emergency Contacts
@app.route("/api/emergency-contacts/<string:user_id>", methods=["GET"])
def get_emergency_contacts(user_id):
    try:
        contacts = EmergencyContacts.query.filter_by(user_id=user_id).all()

        contacts_list = [
            {"id": contact.id, "name": contact.name, "phone": contact.phone}
            for contact in contacts
        ]

        return jsonify(contacts_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/emergency-contacts/<string:user_id>", methods=["POST"])
def add_emergency_contact(user_id):
    try:
        data = request.json
        new_contact = EmergencyContacts(
            user_id=user_id,
            name=data['name'],
            phone=data['phone']
        )
        db.session.add(new_contact)
        db.session.commit()
        return jsonify({"message": "Emergency contact added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/emergency-contacts/<string:user_id>/<int:contact_id>', methods=['DELETE'])
def delete_emergency_contact(user_id, contact_id):
    try:
        contact = EmergencyContacts.query.filter_by(user_id=user_id, id=contact_id).first()
        if contact:
            db.session.delete(contact)
            db.session.commit()
            return jsonify({"message": "Contact deleted successfully."}), 200
        else:
            return jsonify({"error": "Contact not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete contact: {str(e)}"}), 500

# Reports
@app.route("/api/reports/<string:user_id>", methods=["GET"])
def get_reports(user_id):
    try:
        reports = Reports.query.filter_by(user_id=user_id).all()

        reports_list = [
            {"id": report.id, "report_date": report.report_date, "report_probability": report.report_probability, "report_prediction": report.report_prediction}
            for report in reports
        ]

        return jsonify(reports_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/reports/<string:user_id>", methods=["POST"])
def add_report(user_id):
    try:
        data = request.json
        new_report = Reports(
            user_id=user_id,
            report_date=data['report_date'],
            report_probability=data['report_probability'],
            report_prediction=data['report_prediction']
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify({"message": "Report added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 3000)))
