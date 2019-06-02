from __init__ import db, User

db.create_all()
# admin = User(username='admsssasdsasaasddasasdswisan', email='adaminw@sasasasddaadssddaexaasmsple.com')
admin = User(id=6,
             first_name='achilleas',
             last_name='vlogiaris',
             credit=54,
             email='achilleasvlogiaris@gmail.com')

db.session.add(admin)
# db.session.add(guest)
db.session.commit()

# db.drop_all()

print(User.query.all())



