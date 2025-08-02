from mongoengine import Document, DateTimeField, ReferenceField, ListField, ObjectIdField, BooleanField, IntField
from mongoengine.fields import EmbeddedDocumentField, EmbeddedDocument, DictField
from datetime import datetime
from users.models import User
from stories.models import Scenario, Scene, Choice


class HistoryEntry(EmbeddedDocument):
    """
    Entrée d'historique pour suivre les choix d'un joueur
    """
    scene_id = ReferenceField(Scene, required=True)
    choice_id = ReferenceField(Choice)
    timestamp = DateTimeField(default=datetime.utcnow)
    metadata = DictField()  # Données supplémentaires (temps passé, etc.)


class PlayerProgress(Document):
    """
    Modèle pour suivre la progression d'un joueur dans un scénario
    """
    meta = {
        'collection': 'player_progress',
        'indexes': [
            'user_id',
            'scenario_id',
            'current_scene_id',
            ('user_id', 'scenario_id')  # Index composé
        ]
    }
    
    user_id = ReferenceField(User, required=True)
    scenario_id = ReferenceField(Scenario, required=True)
    current_scene_id = ReferenceField(Scene, required=True)
    history = ListField(EmbeddedDocumentField(HistoryEntry))
    is_completed = BooleanField(default=False)
    completed_at = DateTimeField()
    total_time_spent = IntField(default=0)  # Temps total en secondes
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def add_history_entry(self, scene, choice=None, metadata=None):
        """Ajouter une entrée à l'historique"""
        entry = HistoryEntry(
            scene_id=scene,
            choice_id=choice,
            metadata=metadata or {}
        )
        self.history.append(entry)
        self.save()
    
    def get_current_choices(self):
        """Obtenir les choix disponibles pour la scène actuelle"""
        if self.current_scene_id:
            return self.current_scene_id.choices
        return []
    
    def move_to_scene(self, scene, choice=None, metadata=None):
        """Déplacer le joueur vers une nouvelle scène"""
        self.add_history_entry(self.current_scene_id, choice, metadata)
        self.current_scene_id = scene
        
        # Vérifier si c'est une scène de fin
        if scene.is_end_scene:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
        
        self.save()
    
    def get_progress_percentage(self):
        """Calculer le pourcentage de progression"""
        if not self.scenario_id.scenes:
            return 0
        
        total_scenes = len(self.scenario_id.scenes)
        visited_scenes = len(set(entry.scene_id.id for entry in self.history))
        return min(100, (visited_scenes / total_scenes) * 100)
    
    def __str__(self):
        return f"{self.user_id.email} - {self.scenario_id.title} ({self.get_progress_percentage():.1f}%)"
    
    class Meta:
        verbose_name = "Player Progress"
        verbose_name_plural = "Player Progress"
