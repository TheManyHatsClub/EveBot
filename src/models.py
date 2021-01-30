from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()
engine = create_engine('sqlite:///sqlite.db', echo=False, pool_recycle=3600)
sessionfactory = sessionmaker(bind=engine)
Session = scoped_session(sessionfactory)


# A service which contains servers, chats, and users (e.g, 'discord' or 'irc')
class Service(Base):
    __tablename__="service"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __repr__(self):
        return "<Service(name='%s', id='%s')>" % (self.name, self.id)


class User(Base):
    __tablename__="user"

    # Each user is unique within its service
    id = Column(String(50), primary_key=True)
    service_id = Column(ForeignKey('service.id'), primary_key=True)

    username = Column(String(100))

    def __repr__(self):
        return "<User(username='%s', service='%s')>" % (self.username, self.service_id)


class Server(Base):
    __tablename__ = "server"

    # Each server is unique within its service
    id = Column(String(50), primary_key=True)
    service_id = Column(Integer, primary_key=True)

    server_name = Column(String(100))

    def __repr__(self):
        return "<Server(name='%s', service='%s')>" % (
                             self.server_name, self.service_id)


class Chat(Base):
    __tablename__ = "chat"

    # Each chat is unique within a server
    id = Column(String(50), primary_key=True)
    server_id = Column(ForeignKey('server.id'), primary_key=True)

    chat_name = Column(String(100))
    nsfw = Column(Boolean(create_constraint=False))


class TagReactables(Base):
    __tablename__ = "tagreactables"

    message_id = Column(String(20), primary_key=True)
    function_name = Column(String(50))   # Used to find the function to use
    function_args = Column(String(100))  # Used as args to the function (e.g, in order to specify roles to assign)

class Warning(Base):
    __tablename__ = "warning"
    id = Column(String(50), primary_key=True)
    user = Column(ForeignKey('user.id'))
    reason = Column(String(500))

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)

        try:
            session.commit()
        except:
            session.rollback()

        return instance


Base.metadata.create_all(engine)
