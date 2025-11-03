from mongoengine import (
    Document,
    StringField,
    EmailField,
    DateTimeField,
    ReferenceField,
    ListField,
    ObjectIdField,
)
from mongoengine.fields import EmbeddedDocumentField, EmbeddedDocument
from datetime import datetime
import bcrypt


class User(Document):
    """
    Modèle utilisateur pour gérer les admins et les joueurs
    """

    meta = {"collection": "users", "indexes": ["email", "role"]}

    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    role = StringField(required=True, choices=["admin", "player"], default="player")
    first_name = StringField(max_length=100)
    last_name = StringField(max_length=100)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if not self.id:
            # Hash password on creation
            self.password = self.hash_password(self.password)
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        """Check if the provided password matches the hashed password"""
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))

    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == "admin"

    @property
    def is_player(self):
        """Check if user is a player"""
        return self.role == "player"

    def __str__(self):
        return f"{self.email} ({self.role})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
