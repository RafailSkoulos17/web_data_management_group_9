from first import db, User

db.create_all()
admin = User(username='admsssasdsasadasasdswisan', email='adaminw@sasasdaadssddaexaasmsple.com')
guest = User(username='gauswesssasdsadasdsasdst', email='guest@exasdawsasdaasdasdasdmspale.com')

db.session.add(admin)
# db.session.add(guest)
db.session.commit()

# db.drop_all()

print(User.query.all())



