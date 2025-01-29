from sqlite3 import IntegrityError
from __init__ import app, db

class Student(db.Model):
    __tablename__ = 'students'  # Changed table name to 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    favorite_color = db.Column(db.String(50), nullable=False)
    
    def __init__(self, name, age, grade, favorite_color):
        self.name = name
        self.age = age
        self.grade = grade
        self.favorite_color = favorite_color
    
    def create(self):
        try:
            db.session.add(self)  # Prepare to persist object to table
            db.session.commit()  # Commit transaction
            return self
        except IntegrityError:
            db.session.rollback()
            return None
    
    def read(self):
        """
        Converts the user object to a dictionary.
        
        Returns:
            dict: A dictionary representation of the user object.
        """
        data = {
            "name": self.name,
            "age": self.age,
            "grade": self.grade,
            "favorite_color": self.favorite_color,
        }
        return data

    def update(self, inputs):
        """
        Updates the student object with new data.
        
        Args:
            inputs (dict): A dictionary containing the new data for the student.
        
        Returns:
            Student: The updated user object, or None on error.
        """
        if not isinstance(inputs, dict):
            return self

        name = inputs.get("name", "")
        age = inputs.get("age", "")
        grade = inputs.get("grade", "")
        favorite_color = inputs.get("favorite_color", "")

        # Update table with new data
        if name:
            self.name = name
        if age:
            self.age = age
        if grade:
            self.grade = grade
        if favorite_color:
            self.favorite_color = favorite_color
            
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None
        return self

    def restore(data):
        students = {}
        for student_data in data:
            _ = student_data.pop('id', None)  # Remove 'id' from user_data and store it in user_id
            _name = student_data.get("name", None)
            student = Student.query.filter_by(name=_name).first()
            print(type(student))
            if student:
                student.update(student_data)
            else:
                student = Student(**student_data)
                student.create()
        return students



def initStudentData():
    with app.app_context():
        db.create_all()
        # Example student data
        s1 = Student(name='Bailey', age=16, grade="11th", favorite_color="green")
        s2 = Student(name='Ahmad', age=15, grade="10th", favorite_color="blue")
        s3 = Student(name='Nathan', age=16, grade="10th", favorite_color="red")
        students = [s1, s2, s3]
        
        for member in students:
            try:
                member.create()
            except IntegrityError:
                '''fails with bad or duplicate data'''
                db.session.remove()
